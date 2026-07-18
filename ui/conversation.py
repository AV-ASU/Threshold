"""Organic branching NPC conversations (the PI's investigation verb).

Where the old ask-layer showed abstract topic labels ("The girl") and
inferred the question, this drives a real EXCHANGE: the menu options ARE
the PI's own spoken lines, and picking one plays a back-and-forth where
the PI and the NPC each speak in turn, floating over their own heads
(ui/float_speech) so the world keeps running while they talk. An exchange
can branch on an inline choice (show him the photo, or don't), and new
questions open up as the case grows -- the PI learns something, and the
next time he stands at that desk he has a new thing to put to the man.

Only the PICK is modal (it needs the option cursor); every spoken line
floats. The runner is a small state machine wired entirely through the
existing float_speech `on_complete` chain and `dialog.show_choice`
callbacks, so Game does not tick it -- the caption timing already runs in
the main loop, and each line's completion fires the next beat.

A conversation is plain data (see scenes/dialogue.py SABLE_CONVO):

    {
      "id":   "sable",                 # namespaces the once-asked flags
      "name": "Mr. Sable",             # shown over the NPC's float
      "voice":    "blip_low",          # the NPC's blip voice
      "prompt":   "He waits.",         # the modal menu's framing line --
                                       # or a callable(game) -> str, for
                                       # mood-reactive framing (Vane)
      "leave":    "That's all for now.",
      "greet":    {"flag": "sable_greeted",
                   "beats": [("npc", "Sable. I keep the desk here.")]},
      "on_leave": lambda g: [beats] or None,   # a last word as you go
      "exchanges": [ {exchange}, ... ],
    }

`on_leave(game)` fires when the player picks the leave option; if it
returns beats (e.g. a one-time hook), they float and the talk ends.

An EXCHANGE (one askable question):

    {
      "key":    "mara",                # unique within the conversation
      "q":      "I'm looking for a woman. Mara Blaine.",  # the PI's line
      "label":  "I'm looking for someone.",  # optional SHORT menu text --
                                       # the choice box is small; the full
                                       # q still floats as the spoken line
      "avail":  lambda g: True,        # optional; offered only when true
      "once":   True,                  # drops from the menu once asked
      "ends":   True,                  # optional; the talk CLOSES after
                                       # this exchange's beats instead of
                                       # reopening the menu (a walk-away
                                       # beat -- Mara's father card)
      "on_ask": lambda g: ...,         # optional side effect when picked
      "beats":  [ beat, ... ],         # what follows the PI's question;
                                       # may be a callable(game) -> [beat...]
                                       # to vary the reply on game state
    }

A BEAT is one of:
    ("npc", "text")               NPC line, floats over the NPC's head
    ("pi",  "text")               PI line, floats over the player
    ("ask", "prompt",             an inline branch (modal pick)
        [ (label, [beats], on_pick_or_None), ... ])
    ("do",  fn)                   a silent side effect mid-chain: runs
                                  fn(game) and steps straight on (Mara's
                                  unmask reveal rides this)

`name` may also be a callable(game) -> str, so the speaker's LISTING can
change mid-talk (Mara reads as one of the congregation until the unmask).

`on_pick(game)` runs a side effect (set a flag, file a note) when its
option is chosen; its sub-beats splice in ahead of the rest.
"""


class Conversation:
    def __init__(self, game, npc, convo, tableau=False):
        self.game = game
        self.npc = npc
        self.convo = convo
        # When True, the talk is PRESENTED inside a frozen close-up tableau:
        # spoken beats render as the tableau's caption and the menu as the
        # tableau's option panel (game._tableau_caption / _tableau_choices),
        # instead of floating over heads. The state machine is identical.
        self.tableau = tableau
        self.queue = []          # pending beats in the current exchange
        self.current = None      # key of the exchange being played
        self._closing = False    # a leave-hook is playing; do not reopen
        # True from start() until the talk ends (leave picked, the leave
        # hook finishes, or the partner check below breaks it off). The
        # world sim reads this to hold the partner in place (the talk-hold
        # in Scene.update), so it must go False on EVERY exit path.
        self.active = False

    # ---- entry ----------------------------------------------------------
    def start(self):
        """Run the one-time greeting (if unspent), then open the menu."""
        self.active = True
        greet = self.convo.get("greet")
        if greet and not self.game.save.flag(greet["flag"]):
            self.game.save.set_flag(greet["flag"], True)
            self.queue = list(greet["beats"])
            self._step()
        else:
            self._menu()

    # ---- the partner check ----------------------------------------------
    def _partner_here(self):
        """True while the talk still has both parties: the NPC alive and
        outside (not a homebody behind their door), and the player within
        earshot of the desk/counter/step. Checked before the menu REOPENS
        after an exchange -- so walking off mid-answer ends the talk
        quietly instead of yanking the player back into a modal menu from
        across the room. (A stub with no position, as the harnesses use,
        always passes.)"""
        npc = self.npc
        if npc is None:
            return True
        if (not getattr(npc, "alive", True)
                or getattr(npc, "_is_corpse", False)
                or getattr(npc, "_inside", False)):
            return False
        try:
            dx = npc.x - self.game.player.x
            dy = npc.y - self.game.player.y
        except (AttributeError, TypeError):
            return True
        return (dx * dx + dy * dy) <= 72 * 72

    def _end(self):
        self.active = False
        if getattr(self.game, "_convo", None) is self:
            self.game._convo = None
        # A tableau-hosted talk closes its close-up when the talk ends.
        if self.tableau and hasattr(self.game, "_close_tableau"):
            self.game._close_tableau()

    # ---- the question menu ---------------------------------------------
    def _offered(self, ex):
        if ex.get("once") and self.game.save.flag(self._asked_flag(ex["key"])):
            return False
        av = ex.get("avail")
        return av(self.game) if av else True

    def _asked_flag(self, key):
        return f"convo_{self.convo['id']}_{key}_asked"

    def _menu(self):
        avail = [ex for ex in self.convo["exchanges"] if self._offered(ex)]
        # The menu shows the SHORT label when one is authored (the choice
        # box is small); picking it still floats the full q as the PI's
        # spoken line.
        labels = ([ex.get("label", ex["q"]) for ex in avail]
                  + [self.convo.get("leave", "Leave.")])

        # The framing line may be authored as a callable(game) -> str so a
        # conversation can read MOOD into it (Vane's despair/hope ledger,
        # DESIGN.md §2: the player never sees a number, only how he sits).
        prompt = self.convo.get("prompt", "What do you ask?")
        if callable(prompt):
            prompt = prompt(self.game)

        def _pick(idx):
            if idx >= len(avail):
                # Leaving. The NPC may get one last word (a hook the first
                # time you try to go); it floats, then the talk ends.
                hook = self.convo.get("on_leave")
                beats = hook(self.game) if hook else None
                if beats:
                    self._closing = True
                    self.current = None
                    self.queue = list(beats)
                    self._step()
                else:
                    self._end()
                return
            ex = avail[idx]
            self.current = ex["key"]
            # An exchange may carry a side effect fired the moment it is
            # asked (hand over an item, file a note); the beats then narrate
            # what just happened.
            on_ask = ex.get("on_ask")
            if on_ask:
                on_ask(self.game)
            # The PI SPEAKS his question first, then the exchange plays. An
            # exchange's `beats` may be a callable(game) -> [beat...] so the
            # reply can vary on game state (e.g. Sable hints the cellar key
            # only when the PI does not already carry it).
            raw = ex["beats"]
            beats = raw(self.game) if callable(raw) else raw
            self.queue = [("pi", ex["q"])] + list(beats)
            self._step()

        if self.tableau:
            self.game._tableau_choices(prompt, labels, _pick)
        else:
            self.game.dialog.show_choice(
                prompt, labels, _pick,
                speaker="", voice="blip_soft", portrait="narrator")

    # ---- beat playback --------------------------------------------------
    def _speaker(self, who):
        return self.game.player if who == "pi" else self.npc

    def _float(self, who, text):
        name = "" if who == "pi" else self.convo.get("name", "")
        if callable(name):
            name = name(self.game)
        voice = (self.convo.get("pi_voice", "blip_soft") if who == "pi"
                 else self.convo.get("voice", "blip_mid"))
        if self.tableau:
            # In the tableau the line is a caption over the close-up; E
            # advances it, which fires _step (the next beat). The line
            # still SPEAKS: one voice blip at line start (the seats sat
            # mute per-beat before the #2b sound pass -- every other
            # dialogue channel voices its lines).
            self.game.audio.play(voice, 0.5)
            self.game._tableau_caption(who, name, text, self._step)
            return
        # float_speech takes the speaker object directly and fires
        # on_complete when the line finishes (auto after read-time, or E
        # near the speaker) -- which drives the next beat.
        self.game.float_speech.begin(
            self._speaker(who), [text], name=name, voice=voice,
            on_complete=self._step)

    def _step(self):
        # An ended (or replaced -- see open_conversation) talk goes
        # inert: its pending float on_complete must not reopen a menu
        # over whatever superseded it.
        if not self.active:
            return
        if not self.queue:
            # Exchange finished: retire a one-shot question, reopen the menu
            # (or close the talk outright for an "ends" exchange).
            if self.current is not None:
                ex = self._find(self.current)
                if ex and ex.get("once"):
                    self.game.save.set_flag(self._asked_flag(self.current), True)
                ended = bool(ex and ex.get("ends"))
                self.current = None
                if ended:
                    self._end()
                    return
            if self._closing:
                self._closing = False        # leave-hook done; talk ends
                self._end()
                return
            # The partner walked off (or the player did) while the answer
            # played out: end the talk quietly rather than reopening a
            # modal menu across the room.
            if not self._partner_here():
                self._end()
                return
            self._menu()
            return
        beat = self.queue.pop(0)
        kind = beat[0]
        if kind in ("npc", "pi"):
            self._float(kind, beat[1])
        elif kind == "ask":
            self._inline_choice(beat[1], beat[2])
        elif kind == "do":
            # a silent side effect between spoken beats (no caption of its
            # own): run it and step straight on
            beat[1](self.game)
            self._step()
        else:
            self._step()

    def _inline_choice(self, prompt, options):
        def _pick(idx):
            _, sub, on_pick = options[idx]
            if on_pick:
                on_pick(self.game)
            self.queue[0:0] = list(sub)      # splice the branch in ahead
            self._step()
        if self.tableau:
            self.game._tableau_choices(prompt, [o[0] for o in options], _pick)
        else:
            self.game.dialog.show_choice(
                prompt, [o[0] for o in options], _pick,
                speaker="", voice="blip_soft", portrait="narrator")

    def _find(self, key):
        for ex in self.convo["exchanges"]:
            if ex["key"] == key:
                return ex
        return None


def open_conversation(game, npc, convo, tableau=False):
    """Start (or restart) an organic conversation with `npc`. Held on
    `game._convo` so it survives the interact call; the callback chain
    keeps it alive regardless. A replaced conversation (walked from one
    talker to another mid-beat) is deactivated first so its pending
    float callback goes inert instead of clobbering the new talk.

    `tableau=True` presents the talk inside a frozen close-up (the opener
    must already have set `game._tableau`); the beats + menu render there."""
    old = getattr(game, "_convo", None)
    if old is not None:
        old.active = False
    game._convo = Conversation(game, npc, convo, tableau=tableau)
    game._convo.start()
