"""Christmas content for the large-print puzzle book.

Carol lines are from traditional / public-domain carols (all published before 1900), quoted word for word.
"""

TITLE = "Large Print Christmas Puzzle Book"
SUBTITLE = "Sudoku, Word Search, Mazes, Carol Code-Breakers and more"

WORD_SEARCHES = [
    ("Deck the Halls", ["TINSEL", "WREATH", "GARLAND", "ORNAMENT", "LIGHTS", "STAR", "ANGEL", "RIBBON",
                        "BELLS", "CANDLE", "MISTLETOE", "HOLLY"]),
    ("Christmas Baking", ["COOKIES", "GINGERBREAD", "FRUITCAKE", "CINNAMON", "NUTMEG", "SPRINKLES",
                          "FROSTING", "PIE", "FUDGE", "SHORTBREAD", "PUDDING", "PEPPERMINT"]),
    ("Winter Weather", ["SNOWFLAKE", "BLIZZARD", "ICICLE", "FROST", "SLEET", "CHILLY", "FREEZING", "WIND",
                        "FLURRY", "SNOWDRIFT", "COLD", "WINTRY"]),
    ("Santa's Workshop", ["SANTA", "ELVES", "SLEIGH", "REINDEER", "TOYS", "WORKSHOP", "CHIMNEY", "STOCKING",
                          "PRESENTS", "LIST", "NAUGHTY", "NICE"]),
    ("Cozy Christmas Eve", ["FIREPLACE", "COCOA", "BLANKET", "SLIPPERS", "CANDLELIGHT", "STORYBOOK",
                            "PAJAMAS", "MARSHMALLOW", "MITTENS", "QUILT", "LANTERN", "COZY"]),
    ("The Holiday Feast", ["TURKEY", "HAM", "GRAVY", "STUFFING", "CRANBERRY", "POTATOES", "ROLLS", "CARROTS",
                           "EGGNOG", "CIDER", "SPROUTS", "PARSNIPS"]),
    ("Carols and Music", ["CAROL", "CHOIR", "HYMN", "PIANO", "ORGAN", "SINGING", "MELODY", "HARMONY",
                          "CHORUS", "JINGLE", "VIOLIN", "TRUMPET"]),
    ("Gifts and Wrapping", ["WRAPPING", "PAPER", "BOWS", "TAPE", "TAGS", "SCISSORS", "BOX", "SURPRISE",
                            "GIFT", "CARD", "TISSUE", "PACKAGE"]),
    ("Snow Day", ["SNOWMAN", "SLED", "SKATES", "SCARF", "GLOVES", "BOOTS", "CARROT", "IGLOO", "SNOWBALL",
                  "TOBOGGAN", "EARMUFFS", "SHOVEL"]),
    ("Winter Animals", ["PENGUIN", "REINDEER", "OWL", "FOX", "RABBIT", "CARDINAL", "ROBIN", "MOOSE", "SEAL",
                        "WALRUS", "HUSKY", "ERMINE"]),
    ("Christmas Tree Farm", ["PINE", "SPRUCE", "FIR", "NEEDLES", "BRANCH", "TRUNK", "STAND", "SAP",
                             "EVERGREEN", "FOREST", "TOPPER", "BAUBLE"]),
    ("Holiday Traditions", ["ADVENT", "NATIVITY", "CAROLING", "PANTOMIME", "CRACKERS", "YULETIDE", "WASSAIL",
                            "POINSETTIA", "CALENDAR", "MANGER", "CANDLES", "FEAST"]),
]

# (line, carol). Public-domain carols; punctuation kept as printed in common hymnals.
CAROLS = [
    ("SILENT NIGHT, HOLY NIGHT", "Silent Night"),
    ("JINGLE BELLS, JINGLE BELLS, JINGLE ALL THE WAY", "Jingle Bells"),
    ("DECK THE HALLS WITH BOUGHS OF HOLLY", "Deck the Halls"),
    ("JOY TO THE WORLD, THE LORD IS COME", "Joy to the World"),
    ("WE WISH YOU A MERRY CHRISTMAS AND A HAPPY NEW YEAR", "We Wish You a Merry Christmas"),
    ("HARK! THE HERALD ANGELS SING", "Hark! The Herald Angels Sing"),
    ("DASHING THROUGH THE SNOW IN A ONE-HORSE OPEN SLEIGH", "Jingle Bells"),
    ("'TIS THE SEASON TO BE JOLLY", "Deck the Halls"),
    ("ALL IS CALM, ALL IS BRIGHT", "Silent Night"),
    ("O COME, ALL YE FAITHFUL, JOYFUL AND TRIUMPHANT", "O Come, All Ye Faithful"),
    ("GOD REST YE MERRY, GENTLEMEN, LET NOTHING YOU DISMAY", "God Rest Ye Merry, Gentlemen"),
    ("IT CAME UPON THE MIDNIGHT CLEAR", "It Came Upon the Midnight Clear"),
]

# Candidates; make_book keeps only words with no other anagram in the system dictionary.
SCRAMBLE_WORDS = [
    "HOLLY", "SCARF", "FROSTY", "WREATH", "SLEIGH", "EGGNOG", "CHOIR", "IGLOO", "JINGLE", "ICICLE",
    "WINTER", "RIBBON", "SPRUCE", "TURKEY", "COOKIES", "CHIMNEY", "SNOWMAN", "MITTENS", "GARLAND", "PUDDING",
    "LANTERN", "STOCKING", "REINDEER", "ORNAMENT", "CHESTNUT", "BLIZZARD", "CINNAMON", "TOBOGGAN", "SNOWBALL",
    "WRAPPING", "NATIVITY", "MISTLETOE", "FIREPLACE", "FRUITCAKE", "CRANBERRY", "SNOWFLAKE", "PEPPERMINT",
    "NUTCRACKER", "POINSETTIA", "GINGERBREAD",
]
