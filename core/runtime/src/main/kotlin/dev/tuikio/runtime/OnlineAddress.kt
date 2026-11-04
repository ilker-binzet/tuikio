package dev.tuikio.runtime

import java.io.IOException
import java.net.Inet4Address
import java.net.Inet6Address
import java.net.InetAddress

/**
 * Resolves an online game's server for its client (docs/RUNTIME.md, "Online games"). The game
 * clients are static musl programs that can't use Android's resolver, so the app resolves the
 * host and hands the client one address. Only public unicast addresses are accepted: a catalog
 * entry (or a DNS answer) must never point a client at the phone itself or the local network.
 */
object OnlineAddress {
    /** Blocking (DNS): call it off the UI thread. */
    fun resolve(host: String, lookup: (String) -> Array<InetAddress> = InetAddress::getAllByName): String {
        val all = try {
            lookup(host)
        } catch (e: Exception) {
            throw IOException("Couldn't find $host. Are you online?")
        }
        val ok = all.filter { isPublic(it) }
        if (ok.isEmpty()) throw IOException("$host doesn't point to a public internet address; Tuikio won't connect to it.")
        // IPv4 first: phones on IPv6-less networks still get an AAAA answer at times.
        return (ok.firstOrNull { it is Inet4Address } ?: ok.first()).hostAddress!!.substringBefore('%')
    }

    fun isPublic(a: InetAddress): Boolean {
        if (a.isAnyLocalAddress || a.isLoopbackAddress || a.isLinkLocalAddress || a.isSiteLocalAddress || a.isMulticastAddress) return false
        val b = a.address
        return when (a) {
            is Inet4Address -> {
                val o0 = b[0].toInt() and 0xff
                val o1 = b[1].toInt() and 0xff
                !(o0 == 0 || o0 >= 224 ||
                    (o0 == 100 && o1 in 64..127) ||      // carrier-grade NAT
                    (o0 == 192 && o1 == 0 && (b[2].toInt() and 0xff) == 0) ||
                    (o0 == 198 && o1 in 18..19))           // benchmarking
            }
            is Inet6Address -> {
                val o0 = b[0].toInt() and 0xff
                !((o0 and 0xfe) == 0xfc ||                 // unique local fc00::/7
                    (o0 == 0x20 && (b[1].toInt() and 0xff) == 0x01 && (b[2].toInt() and 0xff) == 0x0d && (b[3].toInt() and 0xff) == 0xb8) ||
                    a.isIPv4CompatibleAddress || b.take(12) == List(10) { 0.toByte() } + listOf(0xff.toByte(), 0xff.toByte()))
            }
            else -> false
        }
    }
}
