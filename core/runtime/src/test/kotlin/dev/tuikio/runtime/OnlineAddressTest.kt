package dev.tuikio.runtime

import java.io.IOException
import java.net.InetAddress
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class OnlineAddressTest {
    private fun ip(s: String) = InetAddress.getByName(s)

    @Test
    fun onlyPublicAddresses() {
        for (s in listOf("127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.1.1", "100.64.0.1", "0.0.0.0",
                         "224.0.0.1", "::1", "fe80::1", "fd00::1", "::ffff:10.0.0.1", "2001:db8::1")) {
            assertFalse(OnlineAddress.isPublic(ip(s)), s)
        }
        for (s in listOf("1.1.1.1", "93.184.216.34", "2606:4700::1111")) assertTrue(OnlineAddress.isPublic(ip(s)), s)
    }

    @Test
    fun picksAPublicAddressPreferringIpv4() {
        assertEquals("1.1.1.1", OnlineAddress.resolve("x.example") { arrayOf(ip("2606:4700::1111"), ip("10.0.0.1"), ip("1.1.1.1")) })
        assertEquals("2606:4700:0:0:0:0:0:1111", OnlineAddress.resolve("x.example") { arrayOf(ip("2606:4700::1111")) })
        assertFailsWith<IOException> { OnlineAddress.resolve("x.example") { arrayOf(ip("127.0.0.1"), ip("192.168.0.2")) } }
        assertFailsWith<IOException> { OnlineAddress.resolve("x.example") { throw java.net.UnknownHostException() } }
    }
}
