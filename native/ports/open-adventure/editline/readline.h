/* Stand-in for libedit's <editline/readline.h> (Tuikio): Open Adventure only reads a line with a
 * prompt and adds it to the history. The app's terminal does the line editing (and the phone's
 * keyboard); there is no history. SPDX-License-Identifier: BSD-2-Clause */
#ifndef TUIKIO_EDITLINE_READLINE_H
#define TUIKIO_EDITLINE_READLINE_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static inline char *readline(const char *prompt) {
    char buf[1024];
    if (prompt) {
        fputs(prompt, stdout);
        fflush(stdout);
    }
    if (!fgets(buf, sizeof buf, stdin))
        return NULL;
    buf[strcspn(buf, "\n")] = '\0';
    return strdup(buf);
}

static inline int add_history(const char *line) {
    (void)line;
    return 0;
}
#endif
