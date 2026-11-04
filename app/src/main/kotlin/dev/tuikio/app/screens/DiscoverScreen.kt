package dev.tuikio.app.screens

import android.content.Context
import android.graphics.BitmapFactory
import android.text.TextUtils
import android.view.Gravity
import android.view.View
import android.widget.HorizontalScrollView
import android.widget.ImageView
import android.widget.LinearLayout
import dev.tuikio.app.game.GameLauncher
import dev.tuikio.app.nav.Screen
import dev.tuikio.app.nav.Tab
import dev.tuikio.app.ui.Brands
import dev.tuikio.app.ui.ButtonStyle
import dev.tuikio.app.ui.ChipKind
import dev.tuikio.app.ui.Icon
import dev.tuikio.app.ui.MATCH
import dev.tuikio.app.ui.Motion
import dev.tuikio.app.ui.StatusChip
import dev.tuikio.app.ui.StickerDrawable
import dev.tuikio.app.ui.T
import dev.tuikio.app.ui.TButton
import dev.tuikio.app.ui.Theme
import dev.tuikio.app.ui.WRAP
import dev.tuikio.app.ui.card
import dev.tuikio.app.ui.dp
import dev.tuikio.app.ui.hstack
import dev.tuikio.app.ui.iconButton
import dev.tuikio.app.ui.lp
import dev.tuikio.app.ui.vstack
import dev.tuikio.catalog.DiscoveryEntry

class DiscoverScreen : Screen() {
    override val tab = Tab.DISCOVER
    private var category = "all"

    override fun build(ctx: Context): View = ctx.page {
        val p = Theme.palette
        addView(brandHeader(ctx) { nav.push(SearchScreen()) })

        val recent = app.library.recent?.let { app.catalog.game(it.gameId) }
        if (recent != null && app.catalog.isPlayable(recent)) {
            addView(ctx.card(gapDp = 0) {
                addView(ctx.hstack(14) {
                    addView(MiniScreen(ctx, app.catalog.art(recent), artInk(recent), cells = recent.art), LinearLayout.LayoutParams(ctx.dp(112), ctx.dp(96)))
                    addView(ctx.vstack(6) {
                        addView(T.label(ctx, "Continue"))
                        addView(T.title(ctx, recent.title, 20f).apply { maxLines = 1; ellipsize = TextUtils.TruncateAt.END })
                        val mins = (app.library.entry(recent.id)?.playSeconds ?: 0) / 60
                        addView(T.soft(ctx, if (mins > 0) "$mins min played" else "Picked up recently"))
                        addView(TButton(ctx, "Resume", icon = Icon.PLAY).apply {
                            setOnClickListener { GameLauncher.launch(ctx, recent.id) }
                        }, LinearLayout.LayoutParams(WRAP, WRAP))
                    }, lp(0, WRAP, 1f))
                })
            })
        } else {
            addView(ctx.card(fill = p.surface) {
                addView(ctx.hstack(12) {
                    addView(ImageView(ctx).apply { setImageResource(dev.tuikio.app.R.drawable.kio); contentDescription = "Kio" },
                        LinearLayout.LayoutParams(ctx.dp(84), ctx.dp(84)))
                    addView(ctx.vstack(6) {
                        val n = app.catalog.games.count { app.catalog.isPlayable(it) }
                        addView(T.title(ctx, "Kio carried $n games home", 19f))
                        addView(T.soft(ctx, "They run right here on your phone. No account, no Termux, no typing commands."))
                    }, lp(0, WRAP, 1f))
                })
                addView(TButton(ctx, "Try Kio: Lantern Tide", icon = Icon.PLAY).apply {
                    setOnClickListener { nav.push(DetailsScreen("lantern-tide")) }
                }, lp(MATCH, WRAP))
            })
        }

        // Genre filter: every category the catalog has, with counts; the row scrolls sideways.
        val bundled = app.catalog.games.filter { app.catalog.isBundled(it) }
        addView(categoryChips(ctx, bundled, category) { category = it; nav.rebuild() })
        val games = bundled.filter { inCategory(it, category) }
        sectionHeader("Plays on ${Theme.displayName}", "${games.size} games ›") { nav.push(AllGamesScreen(category)) }
        // A shelf of the first ones, then a card that opens them all.
        addView(ctx.shelf(games.take(SHELF_SIZE), if (games.size > SHELF_SIZE) games.size else null,
            onAll = { nav.push(AllGamesScreen(category)) }) { nav.push(DetailsScreen(it.id)) })

        // Honest "coming" list: discovery links, not installable.
        if (app.prefs.showDiscoverOnly) {
            val upcoming = app.catalog.discoverOnly.filter { it.kind == dev.tuikio.catalog.EntryKind.GAME }
            sectionHeader("Not ported yet", "See all ${upcoming.size}") { nav.push(SearchScreen(onlyDiscover = true)) }
            addView(T.soft(ctx, "Links from the community list. You can browse them; Install appears only after a real port passes its tests."))
            val picks = listOf("brogue-community-edition", "nethack", "dungeon-crawl-stone-soup", "bastet", "tty-solitaire", "nudoku")
                .mapNotNull { id -> upcoming.firstOrNull { it.id == id } }
            picks.forEach { addView(discoveryRow(ctx, it) { nav.push(DiscoveryEntryScreen(it.id)) }) }
        }

        addView(ctx.card(fill = if (p.isDark) p.surfaceAlt else p.ink) {
            val onDark = if (p.isDark) p.ink else p.ground
            addView(T.label(ctx, "Did you know", if (p.isDark) p.inkSoft else p.accent2))
            addView(T.title(ctx, "Every game keeps its own terminal", 19f, onDark))
            addView(T.body(ctx, "Games run as real programs in a private terminal Tuikio draws for you. Controls send exactly the keys the game expects, so the rules never change.", 15f, onDark))
        })
    }
}

private const val SHELF_SIZE = 12

/** "online" is a filter of its own (network games); the rest are manifest categories. */
fun inCategory(g: dev.tuikio.catalog.GameManifest, c: String) = when (c) {
    "all" -> true
    "online" -> g.online != null
    else -> g.category == c && g.online == null
}

/** One sideways-scrolling row of category chips, each with its game count. */
fun categoryChips(ctx: Context, games: List<dev.tuikio.catalog.GameManifest>, selected: String, onPick: (String) -> Unit): View {
    val order = listOf("arcade", "puzzle", "roguelike", "adventure", "strategy", "cards", "words", "simulation")
    val cats = listOf("all") + order.filter { c -> games.any { inCategory(it, c) } } +
        (if (games.any { it.online != null }) listOf("online") else emptyList())
    val row = ctx.hstack(8) {
        setPadding(0, 0, ctx.dp(18), ctx.dp(4))
        cats.forEach { c ->
            val n = games.count { inCategory(it, c) }
            val label = c.replaceFirstChar { it.uppercase() }
            addView(TButton(ctx, "$label $n", if (c == selected) ButtonStyle.MINT else ButtonStyle.SECONDARY).apply {
                minHeight = ctx.dp(44)
                contentDescription = "$label, $n games" + if (c == selected) ", selected" else ""
                setOnClickListener { onPick(c) }
            })
        }
    }
    return HorizontalScrollView(ctx).apply {
        isHorizontalScrollBarEnabled = false
        clipToPadding = false
        addView(row)
        // Keep the selected chip in view after a rebuild.
        post {
            val i = cats.indexOf(selected)
            if (i > 0) row.getChildAt(i)?.let { smoothScrollTo((it.left - ctx.dp(24)).coerceAtLeast(0), 0) }
        }
    }
}

/** Every playable game, two to a row, filtered by category: what "N games" opens. */
class AllGamesScreen(private var category: String = "all") : Screen() {
    override val tab = Tab.DISCOVER

    override fun build(ctx: Context): View = ctx.page(gapDp = 14) {
        val bundled = app.catalog.games.filter { app.catalog.isBundled(it) }.sortedBy { it.title.lowercase() }
        topBar(nav, "All games")
        addView(categoryChips(ctx, bundled, category) { category = it; nav.rebuild() })
        val games = bundled.filter { inCategory(it, category) }
        addView(T.soft(ctx, "${games.size} games · A to Z"))
        games.chunked(2).forEach { pair ->
            addView(ctx.hstack(14) {
                pair.forEach { g -> addView(Cartridge(ctx, g) { nav.push(DetailsScreen(g.id)) }, lp(0, WRAP, 1f)) }
                if (pair.size == 1) addView(View(ctx), lp(0, 1, 1f))
            })
        }
    }
}

/** Header with the active brand's mark and name (or the Tuikio wordmark) plus search. */
fun brandHeader(ctx: Context, onSearch: () -> Unit): View = ctx.hstack(10) {
    val custom = Theme.custom
    val logo = custom?.logoFile
    addView(ImageView(ctx).apply {
        if (logo != null) setImageBitmap(BitmapFactory.decodeFile(logo.absolutePath))
        else setImageResource(Theme.pack.iconRes)
        contentDescription = "${Theme.displayName} logo"
        clipToOutline = true
        outlineProvider = object : android.view.ViewOutlineProvider() {
            override fun getOutline(view: View, outline: android.graphics.Outline) = outline.setOval(0, 0, view.width, view.height)
        }
    }, LinearLayout.LayoutParams(ctx.dp(42), ctx.dp(42)))
    if (custom == null && Theme.pack == Brands.TUIKIO && !Theme.phosphor) {
        addView(ImageView(ctx).apply {
            // Two drawn variants rather than a tint, so the coral cursor dots keep their color.
            setImageResource(if (Theme.palette.isDark) dev.tuikio.app.R.drawable.wordmark_tuikio_light else dev.tuikio.app.R.drawable.wordmark_tuikio)
            contentDescription = "Tuikio"
            adjustViewBounds = true
        }, LinearLayout.LayoutParams(WRAP, ctx.dp(26)))
    } else {
        addView(T.title(ctx, Theme.displayName, 22f).apply { maxLines = 1; ellipsize = TextUtils.TruncateAt.END }, lp(WRAP, WRAP))
    }
    addView(View(ctx), lp(0, 1, 1f))
    addView(ctx.iconButton(Icon.SEARCH, "Search games") { onSearch() })
}

fun discoveryRow(ctx: Context, e: DiscoveryEntry, onClick: () -> Unit): View = ctx.hstack(12) {
    val p = Theme.palette
    background = StickerDrawable(ctx, fill = p.surface, shadowDp = 0f, outline = p.hairline, outlineDp = 2f, cornerDp = 18f)
    setPadding(ctx.dp(14), ctx.dp(12), ctx.dp(12), ctx.dp(12))
    isClickable = true
    isFocusable = true
    contentDescription = "${e.title}, discover only. Opens details."
    setOnClickListener { onClick() }
    addView(ctx.vstack(2) {
        addView(T.body(ctx, e.title, 16f, p.ink, 800).apply { maxLines = 1; ellipsize = TextUtils.TruncateAt.END })
        addView(T.soft(ctx, e.category.replaceFirstChar { it.uppercase() } + " · " + e.kind.id.replace('_', ' '), 13f))
    }, lp(0, WRAP, 1f))
    addView(StatusChip(ctx, "Discover only", ChipKind.DISCOVER, small = true))
    Motion.enter(this)
    gravity = Gravity.CENTER_VERTICAL
}
