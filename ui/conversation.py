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
      "prompt":   "He waits.",         # the modal menu's framing line
      "leave":    "That's all for now.",
      "greet":    {"flag": "sable_greeted",
                   "beats": [("npc", "Sable. I keep the desk here.")]},
      "exchanges": [ {exchange}, ... ],
    }

An EXCHANGE (one askable question):

    {
      "key":   "mara",                 # unique within the conversation
      "q":     "I'm looking for a woman. Mara Blaine.",   # the PI's line
      "avail": lambda g: True,         # optional; offered only when true
      "once":  True,                   # drops from the menu once asked
      "beats": [ beat, ... ],          # what follows the PI's question
    }

A BEAT is one of:
    ("npc", "text")               NPC line, floats over the NPC's head
    ("pi",  "text")               PI line, floats over the player
    ("ask", "prompt",             an inline branch (modal pick)
        [ (label, [beats], on_pick_or_None), ... ])

`on_pick(game)` runs a side effect (set a flag, file a note) when its
option is chosen; its sub-beats splice in ahead of the rest.
"""


class Conversation:
    def __init__(self, game, npc, convo):
        self.game = game
        self.npc = npc
        self.convo = convo
        self.queue = []          # pending beats in the current exchange
        self.current = None      # key of the exchange being played

    # ---- entry ----------------------------------------------------------
    def start(self):
        """Run the one-time greeting (if unspent), then open the menu."""
        greet = self.convo.get("greet")
        if greet and not self.game.save.flag(greet["flag"]):
            self.game.save.set_flag(greet["flag"], True)
            self.queue = list(greet["beats"])
            self._step()
        else:
            self._menu()

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
        labels = [ex["q"] for ex in avail] + [self.convo.get("leave", "Leave.")]

        def _pick(idx):
            if idx >= len(avail):
                return                       # left; E reopens the menu
            ex = avail[idx]
            self.current = ex["key"]
            # The PI SPEAKS his question first, then the exchange plays.
            self.queue = [("pi", ex["q"])] + list(ex["beats"])
            self._step()

        self.game.dialog.show_choice(
            self.convo.get("prompt", "What do you ask?"),
            labels, _pick, speaker="", voice="blip_soft", portrait="narrator")

    # ---- beat playback --------------------------------------------------
    def _speaker(self, who):
        return self.game.player if who == "pi" else self.npc

    def _float(self, who, text):
        name = "" if who == "pi" else self.convo.get("name", "")
        voice = (self.convo.get("pi_voice", "blip_soft") if who == "pi"
                 else self.convo.get("voice", "blip_mid"))
        # float_speech takes the speaker object directly and fires
        # on_complete when the line finishes (auto after read-time, or E
        # near the speaker) -- which drives the next beat.
        self.game.float_speech.begin(
            self._speaker(who), [text], name=name, voice=voice,
            on_complete=self._step)

    def _step(self):
        if not self.queue:
            # Exchange finished: retire a one-shot question, reopen the menu.
            if self.current is not None:
                ex = self._find(self.current)
                if ex and ex.get("once"):
                    self.game.save.set_flag(self._asked_flag(self.current), True)
                self.current = None
            self._menu()
            return
        beat = self.queue.pop(0)
        kind = beat[0]
        if kind in ("npc", "pi"):
            self._float(kind, beat[1])
        elif kind == "ask":
            self._inline_choice(beat[1], beat[2])
        else:
            self._step()

    def _inline_choice(self, prompt, options):
        def _pick(idx):
            _, sub, on_pick = options[idx]
            if on_pick:
                on_pick(self.game)
            self.queue[0:0] = list(sub)      # splice the branch in ahead
            self._step()
        self.game.dialog.show_choice(
            prompt, [o[0] for o in options], _pick,
            speaker="", voice="blip_soft", portrait="narrator")

    def _find(self, key):
        for ex in self.convo["exchanges"]:
            if ex["key"] == key:
                return ex
        return None


def open_conversation(game, npc, convo):
    """Start (or restart) an organic conversation with `npc`. Held on
    `game._convo` so it survives the interact call; the callback chain
    keeps it alive regardless."""
    game._convo = Conversation(game, npc, convo)
    game._convo.start()
