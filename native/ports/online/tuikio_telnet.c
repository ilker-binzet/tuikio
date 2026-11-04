/* Tuikio's telnet client for online games (libgame_telnet.so; native/recipes/online.py).
 *
 * Usage: game_telnet <host> <port>, with TUIKIO_ADDR set to the address the app resolved for
 * <host> (a static musl program can't use Android's resolver; the app also refuses private
 * addresses). It connects there, switches the terminal to raw mode and relays bytes, answering
 * the few telnet options a game server asks about: terminal type (xterm-256color), window size,
 * echo and suppress-go-ahead. Every other option is refused. It ends when either side closes. */
#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <termios.h>
#include <unistd.h>

enum { IAC = 255, DONT = 254, DO = 253, WONT = 252, WILL = 251, SB = 250, SE = 240 };
enum { O_ECHO = 1, O_SGA = 3, O_TTYPE = 24, O_NAWS = 31 };

static int sock = -1;
static struct termios saved;
static int have_saved;
static volatile sig_atomic_t winch = 1;
static unsigned char sent_will[256], sent_do[256];

static void restore(void) {
    if (have_saved) tcsetattr(0, TCSAFLUSH, &saved);
}

static void on_winch(int sig) { (void)sig; winch = 1; }

static void put(const unsigned char *b, size_t n) {
    while (n > 0) {
        ssize_t w = write(sock, b, n);
        if (w < 0) { if (errno == EINTR) continue; exit(0); }
        b += w; n -= (size_t)w;
    }
}

static void opt(int verb, int o) { unsigned char b[3] = {IAC, (unsigned char)verb, (unsigned char)o}; put(b, 3); }

static void send_naws(void) {
    struct winsize ws;
    if (!sent_will[O_NAWS] || ioctl(0, TIOCGWINSZ, &ws) != 0) return;
    unsigned char b[16]; size_t n = 0;
    unsigned char v[4] = {(unsigned char)(ws.ws_col >> 8), (unsigned char)ws.ws_col,
                          (unsigned char)(ws.ws_row >> 8), (unsigned char)ws.ws_row};
    b[n++] = IAC; b[n++] = SB; b[n++] = O_NAWS;
    for (int i = 0; i < 4; i++) { b[n++] = v[i]; if (v[i] == IAC) b[n++] = IAC; }
    b[n++] = IAC; b[n++] = SE;
    put(b, n);
}

/* Answers one negotiation; only replies when our state changes (no loops). */
static void negotiate(int verb, int o) {
    switch (verb) {
    case DO:
        if (o == O_TTYPE || o == O_NAWS) {
            if (sent_will[o] != 1) { sent_will[o] = 1; opt(WILL, o); }
            if (o == O_NAWS) send_naws();
        } else if (sent_will[o] != 2) { sent_will[o] = 2; opt(WONT, o); }
        break;
    case DONT:
        if (sent_will[o] == 1) { sent_will[o] = 2; opt(WONT, o); }
        break;
    case WILL:
        if (o == O_ECHO || o == O_SGA) { if (sent_do[o] != 1) { sent_do[o] = 1; opt(DO, o); } }
        else if (sent_do[o] != 2) { sent_do[o] = 2; opt(DONT, o); }
        break;
    case WONT:
        if (sent_do[o] != 2) { sent_do[o] = 2; opt(DONT, o); }
        break;
    }
}

int main(int argc, char **argv) {
    if (argc != 3) { fputs("usage: game_telnet <host> <port>\n", stderr); return 64; }
    const char *addr = getenv("TUIKIO_ADDR");
    if (!addr || !*addr) addr = argv[1];
    printf("Connecting to %s (port %s)...\r\n", argv[1], argv[2]);
    fflush(stdout);

    struct addrinfo hints = {0}, *res;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_NUMERICHOST | AI_NUMERICSERV;
    if (getaddrinfo(addr, argv[2], &hints, &res) != 0) { printf("Bad address: %s\r\n", addr); return 68; }
    sock = socket(res->ai_family, SOCK_STREAM, 0);
    if (sock < 0 || connect(sock, res->ai_addr, res->ai_addrlen) != 0) {
        printf("Could not connect: %s\r\n", strerror(errno));
        return 69;
    }
    freeaddrinfo(res);

    if (tcgetattr(0, &saved) == 0) {
        have_saved = 1;
        atexit(restore);
        struct termios raw = saved;
        cfmakeraw(&raw);
        tcsetattr(0, TCSAFLUSH, &raw);
    }
    signal(SIGWINCH, on_winch);
    signal(SIGPIPE, SIG_IGN);

    enum { DATA, GOT_IAC, GOT_VERB, IN_SB, SB_IAC } st = DATA;
    int verb = 0, sbopt = -1, sblen = 0;
    unsigned char in[4096], out[8192];
    struct pollfd fds[2] = {{.fd = 0, .events = POLLIN}, {.fd = sock, .events = POLLIN}};
    for (;;) {
        if (winch) { winch = 0; send_naws(); }
        if (poll(fds, 2, -1) < 0) { if (errno == EINTR) continue; break; }
        if (fds[1].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t n = read(sock, in, sizeof in);
            if (n <= 0) break;
            size_t m = 0;
            for (ssize_t i = 0; i < n; i++) {
                int c = in[i];
                switch (st) {
                case DATA: if (c == IAC) st = GOT_IAC; else out[m++] = (unsigned char)c; break;
                case GOT_IAC:
                    if (c == IAC) { out[m++] = IAC; st = DATA; }
                    else if (c >= WILL) { verb = c; st = GOT_VERB; }
                    else if (c == SB) { sbopt = -1; sblen = 0; st = IN_SB; }
                    else st = DATA;
                    break;
                case GOT_VERB: negotiate(verb, c); st = DATA; break;
                case IN_SB:
                    if (c == IAC) st = SB_IAC;
                    else { if (sblen == 0) sbopt = c; else if (sblen == 1 && sbopt == O_TTYPE && c == 1 && sent_will[O_TTYPE] == 1) sbopt = 1000; sblen++; }
                    break;
                case SB_IAC:
                    if (c == SE) {
                        if (sbopt == 1000) {  /* TTYPE SEND: answer IS xterm-256color */
                            static const unsigned char is[] = {IAC, SB, O_TTYPE, 0, 'X','T','E','R','M','-','2','5','6','C','O','L','O','R', IAC, SE};
                            put(is, sizeof is);
                        }
                        st = DATA;
                    } else st = IN_SB;
                    break;
                }
                if (m > sizeof out - 2) { if (write(1, out, m) < 0) return 0; m = 0; }
            }
            if (m && write(1, out, m) < 0) return 0;
        }
        if (fds[0].revents & (POLLIN | POLLHUP)) {
            ssize_t n = read(0, in, sizeof in);
            if (n <= 0) break;
            size_t m = 0;
            for (ssize_t i = 0; i < n; i++) {
                out[m++] = in[i];
                if (in[i] == IAC) out[m++] = IAC;
                else if (in[i] == '\r') out[m++] = 0;  /* NVT: a bare CR is CR NUL */
            }
            put(out, m);
        }
    }
    restore();
    have_saved = 0;
    printf("\r\nConnection closed.\r\n");
    return 0;
}
