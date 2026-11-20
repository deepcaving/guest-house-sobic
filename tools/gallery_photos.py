#!/usr/bin/env python3
"""The gallery: the order of the photographs and their alt texts.

Every photograph is listed here once, in the order it appears in the
gallery. The id is the file name in the photo pack that Milka sent
(Yandex Disk, "Guest House Sobic, Sipovo (updated prices 2027).zip");
each id exists there in two sizes:

    <id>.jpg       the large one - shown when a visitor opens a photo
    <id> (1).jpg   the small one - the grid, and the phone view

The order is deliberate: the house and the rooms first (that is what a
guest books), then the terrace and the flowers, then the water and the
fishing, then the valley and the seasons, and the table and the guests
last. The first pictures are the ones a visitor sees on the phone.

The alt texts are plain English, like the rest of the picture captions
on the site. A blind visitor gets a sentence, not a file name.

    python3 tools/build_gallery.py <the extracted photo folder>
"""

# (id, alt text) - the order of this list is the order of the gallery.
PHOTOS = [
    # --- the house and the rooms -------------------------------------
    ("208820187", "The house from the garden: the peach-coloured facade, the balcony "
                  "overlooking the valley and the flowers along the rail"),
    ("889835199", "The terrace on the lawn above the water, with the seats facing the river"),
    ("889648627", "The seating on the terrace by the water, with the flower bed along the rail"),
    ("686104005", "The living room, with the glass doors that open onto the terrace"),
    ("370664812", "A corner of the sitting room: the black chair, the sofa and the window "
                 "with the view"),
    ("363663779", "A twin room with two single beds and purple covers"),
    ("468412209", "A double room with two beds and a wooden floor"),
    ("373277774", "A room with a sofa, a chair and a table by the window"),
    ("468417589", "A single room with a bed, a bench and a picture on the wall"),
    ("468412972", "The shared kitchen, with the stove, the microwave and the fridge"),
    ("373277852", "The bathroom, with the shower and the white tiles"),
    ("52807899", "The house from the road, behind the stone wall and the trees"),
    ("266119461", "The garden path that leads to the house"),
    ("373277993", "The house seen from the garden, with the balcony above the lawn"),
    ("266763771", "The side of the house with the covered terrace and the old tree"),
    ("266763830", "The house across the meadow, with the hills behind"),
    ("96269301", "The house at the edge of the field, with the mountains beyond"),
    ("121171072", "The house and the meadow that runs down to the water"),
    ("111507303", "The lawn at the back of the house, with the flower beds"),

    # --- the terrace, the porch and the flowers ----------------------
    ("266763874", "The balcony with the pink flowers, above the road"),
    ("320486024", "The porch, with the flowers along the rail"),
    ("320486152", "The window box of the house, full of flowers"),
    ("320486252", "The balcony of the house and the flowers on it"),
    ("469665733", "The baskets of flowers on the terrace rail, above the water"),
    ("583523598", "A pot of flowers on the edge of the water"),
    ("736239969", "The balcony flowers over the calm green water"),
    ("725911054", "The terrace with the flower beds along the edge"),
    ("906066914", "The garden and the flowers down by the water"),
    ("52808116", "The timber pergola with the flowers hanging from it"),
    ("52808722", "The table under the vine, in the shade"),
    ("52808725", "The house with the vine grown over the pergola"),
    ("52808505", "Petunias by the river, with the water behind them"),
    ("266866463", "The lawn with the flowers and the wooded hills beyond"),

    # --- the water and the fishing -----------------------------------
    ("78061429", "The angler with the brown trout he has just caught in the Pliva"),
    ("121170903", "The river flat below the house, with the pavilion in the meadow"),
    ("78061464", "The Pliva below the house, with the hills behind"),
    ("66649066", "The water with the mountains on the far side"),
    ("66646524", "The bend in the Pliva in summer, with the trees on the bank"),
    ("121172580", "The river bend and the gravel bar"),
    ("121172433", "The bend of the river in autumn"),
    ("116348074", "The bank of the river in autumn"),
    ("121171102", "The river below the house in autumn colours"),
    ("121170837", "The river with the trees in autumn colour"),
    ("66646659", "The Pliva in autumn, the water still and clear"),
    ("66649072", "The meadow by the river under a wide sky"),
    ("121171283", "The house on the bank of the river"),
    ("114000976", "The wooded bank of the river"),
    ("66649076", "The path through the forest down to the water"),
    ("66649064", "The meadow and the hills above the valley"),
    ("266866620", "The meadow of the valley with the hills behind"),
    ("302405089", "The flower bed with the hills of the valley behind"),
    ("208819852", "The roses in the field with the valley beyond"),
    ("322154964", "The lawn of the house with the hills of the valley"),

    # --- the spring, the cascades and the seasons ---------------------
    ("95484268", "The Pliva spring: mossy cascades with the flowers on the stones"),
    ("95484389", "The cascade of the spring between the mossy stones"),
    ("203328782", "The cascades of the spring under the trees"),
    ("203328827", "The spring running over the stones in the forest"),
    ("66646908", "The waterfall of the Pliva in the forest"),
    ("116341870", "The rapids of the Pliva"),
    ("116341872", "The river running fast over the stones"),
    ("78061445", "The green meadow and the river in spring, below the hills"),
    ("66649069", "A wide sky over the river and the trees"),
    ("334824955", "The sun over the water"),
    ("334824890", "The water in the morning mist"),
    ("599732071", "The green water with the trees along the bank"),
    ("482700773", "The green river with the hut on the bank"),
    ("806402030", "The sun low over the water"),
    ("806401918", "The snow on the peak above the valley"),
    ("806402109", "The frozen lake and the snow-covered slopes"),
    ("66649095", "The river in winter, with snow on the banks"),
    ("66649105", "The valley in autumn, with the mist coming down"),
    ("374279455", "The lake in the autumn colours"),
    ("374279588", "The hills in autumn colour"),
    ("444434133", "The river in the autumn forest"),
    ("121170981", "The lake with the mountains behind it"),

    # --- the table, the food and the guests --------------------------
    ("889649045", "The table laid for dinner, with roses and hearts"),
    ("154664179", "A table of local food, set for the meal"),
    ("690548676", "The vase of roses and the hearts on the dining table"),
    ("78061421", "The guests at the long table, with the meal and the wine"),
    ("52808515", "A glass of the local white wine, with the flowers behind"),
    ("85225399", "A guest at the table on the terrace"),
    ("371748472", "A guest on the riverbank below the house"),
    ("66658638", "Four pictures of the valley in one frame: the forest path, the angler "
                 "casting, the autumn valley and the dandelions"),
    ("66658990", "Four pictures of the Pliva in one frame: the cascade, the wildflowers, "
                 "the autumn bank and the spring"),
]
