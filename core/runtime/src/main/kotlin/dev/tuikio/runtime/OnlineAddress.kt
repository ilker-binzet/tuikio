package dev.tuikio.runtime

import java.io.IOException
import java.net.Inet4Address
import java.net.Inet6Address
import java.net.InetAddress

/**
 * Resolves an online game's server for its client (docs/RUNTIME.md, "Online games"). The game
 * clients are static musl programs that can't use Android's resolver, so the app resolves the
 * host and hands the client one address. Only public unicast addresses are accepted: a catalog
 * entry (or a DNS answer) must never point a client at the phone itself or the local network
 * (loopback, 10/8, 172.16/12, 192.168/16, link-local, unique-local IPv6).
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
        if (ok.isEmpty()) {
            val seen = all.joinToString { it.hostAddress?.substringBefore('%') ?: "?" }
            throw IOException("$host resolved to $seen, an address on this phone or its local network, so Tuikio won't connect. " +
                "A DNS filter or Private DNS setting may be blocking it.")
        }
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
                // 100.64/10 (Tailscale, carrier NAT) and 198.18/15 ("fake IP" of Clash, v2ray,
                // sing-box VPN apps) are allowed: a VPN on the phone maps them to the real server,
                // and they are never a home or office network.
                !(o0 == 0 || o0 >= 224 ||
                    (o0 == 192 && o1 == 0 && (b[2].toInt() and 0xff) == 0))
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
