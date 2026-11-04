package dev.tuikio.runtime

import dev.tuikio.catalog.GameManifest
import org.junit.jupiter.api.Assumptions.assumeTrue
import java.io.ByteArrayOutputStream
import java.io.File
import java.net.InetAddress
import java.net.ServerSocket
import java.nio.file.Files
import kotlin.concurrent.thread
import kotlin.test.Test
import kotlin.test.assertTrue

/**
 * The telnet client of the online games against a local server: it connects to the address the
 * app passes (TUIKIO_ADDR), not to the host name; answers terminal type and window size; shows
 * the server's output and sends the player's keys. (The SSH client, Dropbear, was checked by hand
 * against a local Dropbear server: see docs/RUNTIME.md, "Online games".)
 */
class OnlineClientsTest {
    private val root = generateSequence(File(System.getProperty("user.dir")).absoluteFile) { it.parentFile }.first { File(it, "catalog/games").isDirectory }
    private val out = File(root, "native/build/out/x86_64")

    @Test
    fun telnetClientTalksToItsServer() {
        val exe = File(out, "libgame_telnet.so")
        if (System.getProperty("tuikio.requireNative") == "true") assertTrue(exe.canExecute(), "${exe.name} missing")
        else assumeTrue(exe.canExecute())
        val m = GameManifest.parse(File(root, "catalog/games/telehack-z-code-games.json").readText())
        val server = ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))
        val received = ByteArrayOutputStream()
        val t = thread {
            server.accept().use { c ->
                val o = c.getOutputStream()
                // DO TTYPE, DO NAWS, WILL ECHO, WILL SGA; then ask for the terminal type.
                o.write(byteArrayOf(-1, -3, 24, -1, -3, 31, -1, -5, 1, -1, -5, 3, -1, -6, 24, 1, -1, -16))
                o.write("Welcome to the test server\r\n> ".toByteArray())
                o.flush()
                val inp = c.getInputStream()
                val buf = ByteArray(256)
                val deadline = System.currentTimeMillis() + 8000
                while (System.currentTimeMillis() < deadline && !received.toString(Charsets.ISO_8859_1).contains("zork")) {
                    val n = inp.read(buf)
                    if (n < 0) break
                    received.write(buf, 0, n)
                }
                o.write("You are standing in an open field.\r\n".toByteArray())
                o.flush()
                Thread.sleep(300)
            }
        }
        val local = m.copy(online = m.online!!.copy(port = server.localPort))
        val home = Files.createTempDirectory("online-").toFile()
        val s = GameSession(LaunchSpec.forManifest(local, out, home, "127.0.0.1"), 80, 24)
        s.start()
        try {
            assertTrue(s.awaitScreen(5000) { l -> l.any { "Welcome to the test server" in it } }, s.screenText().joinToString("\n"))
            s.send("zork\r".toByteArray())
            assertTrue(s.awaitScreen(5000) { l -> l.any { "open field" in it } }, s.screenText().joinToString("\n"))
            t.join(5000)
            val got = received.toByteArray()
            val text = String(got, Charsets.ISO_8859_1)
            assertTrue("XTERM-256COLOR" in text, "terminal type not sent: $text")
            // NAWS: IAC SB 31 0 80 0 24 IAC SE
            assertTrue(text.contains(String(byteArrayOf(-1, -6, 31, 0, 80, 0, 24, -1, -16), Charsets.ISO_8859_1)), "window size not sent")
            assertTrue("zork\r\u0000" in text, "typed line not sent as NVT: $text")
            assertTrue(s.awaitScreen(3000) { l -> l.any { "Connection closed" in it } })
        } finally {
            s.stop(500)
            server.close()
        }
    }
}
