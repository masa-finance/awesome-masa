import asyncio
import json
import logging
import random
from typing import Dict, Optional, List
from openai import OpenAIError
from pydantic import BaseModel, ValidationError
from .client import OpenAIClient
from .utils import parse_prompt_response


class PromptTemplate(BaseModel):
    """
    A Pydantic model representing the structure of the image prompt.

    Attributes:
        difficulty_level (str): The difficulty level of the image ('Easy', 'Medium', 'Hard').
        rating (int): The numerical rating of the difficulty level (1-10).
        complexity_level (str): The complexity description based on difficulty ('simple', 'moderately detailed', 'highly intricate').
        scene_description (str): Description of the scene to be illustrated.
        hidden_object_size (str): The size of the hidden object ('large', 'medium-sized', 'small').
        hidden_object_description (str): Description of the hidden object.
        visibility_instructions (str): Instructions on how the hidden object should be concealed.
        lighting_instructions (str): Instructions on the lighting and color to affect visibility.
        mood (str): The overall mood of the scene ('cheerful', 'lively', 'mysterious').
        desired_interaction (str): What the viewer is encouraged to do ('easily find the object', 'explore the scene', 'carefully search').
        number_of_hidden_objects (int): The number of hidden objects to include in the scene.
    """

    difficulty_level: str
    rating: int
    complexity_level: str
    scene_description: str
    hidden_object_size: str
    hidden_object_description: str
    visibility_instructions: str
    lighting_instructions: str
    mood: str
    desired_interaction: str
    number_of_hidden_objects: int  # New attribute added

    @staticmethod
    def determine_difficulty_level(rating: int) -> str:
        """
        Determines the difficulty level based on the provided rating.

        Args:
            rating (int): The numerical rating (1-10).

        Returns:
            str: The difficulty level ('Easy', 'Medium', 'Hard').
        """
        if rating <= 3:
            return 'Easy'
        elif rating <= 6:
            return 'Medium'
        else:
            return 'Hard'

    @staticmethod
    def determine_complexity(rating: int) -> str:
        """
        Determines the complexity level based on the provided rating.

        Args:
            rating (int): The numerical rating (1-10).

        Returns:
            str: The complexity description ('simple', 'moderately detailed', 'highly intricate').
        """
        if rating <= 3:
            return 'simple'
        elif rating <= 6:
            return 'moderately detailed'
        else:
            return 'highly intricate'

    def generate_prompt(self) -> str:
        """
        Generates the image prompt based on the provided attributes.

        Dynamically adjusts the difficulty level and complexity based on the rating.

        Returns:
            str: A formatted string that can be used as a prompt for image generation.
        """
        # Determine difficulty and complexity based on rating
        self.difficulty_level = self.determine_difficulty_level(self.rating)
        self.complexity_level = self.determine_complexity(self.rating)

        # Determine standard vocabulary based on difficulty
        visibility_actions = {
            'Easy': 'enhance',
            'Medium': 'balance',
            'Hard': 'reduce'
        }
        visibility_action = visibility_actions.get(self.difficulty_level, 'enhance')

        # Construct the prompt string with the number of hidden objects
        prompt = (
            f"Difficulty Level: {self.difficulty_level} ({self.rating}/10)\n\n"
            f"Create a {self.complexity_level}, cartoon-style illustration of {self.scene_description}. "
            f"Hide {self.number_of_hidden_objects} {self.hidden_object_size}, {self.hidden_object_description} somewhere in the scene. "
            f"The objects should {self.visibility_instructions}. "
            f"Use {self.lighting_instructions} to {visibility_action} their visibility. "
            f"The overall mood should be {self.mood}, encouraging viewers to {self.desired_interaction}."
        )
        return prompt


class PromptGenerator:
    """
    A class to generate structured prompts for AI image generation models.

    Attributes:
        client (OpenAIClient): Instance of the OpenAI client.
        themes (List[Dict[str, List[str]]]): A list of themes with possible variations.
        standard_vocabulary (Dict[str, Dict[str, str]]): Standard vocabulary options based on difficulty levels.
    """

    def __init__(self, client: OpenAIClient):
        """
        Initialize the PromptGenerator.

        Args:
            client (OpenAIClient): Instance of OpenAIClient.
        """
        self.client = client
        logging.info("PromptGenerator initialized.")

        self.themes = [
        {
            "name": "Beach",
            "scene_descriptions": [
                "a sunny beach with clear blue skies, umbrellas, and people enjoying the sand and sea",
                "a tranquil beach at sunset with waves gently crashing on the shore and seagulls flying overhead",
                "a lively beach scene with volleyball games, colorful beach towels, and bright sun umbrellas"
            ],
            "hidden_object_descriptions": ["a blue seashell", "a red bucket", "a yellow beach ball"]
        },
        {
            "name": "Park",
            "scene_descriptions": [
                "a lively city park with diverse trees, walking paths, and people engaging in various activities",
                "a peaceful park setting with a pond, ducks, and families having picnics",
                "a bustling park scene with joggers, cyclists, and children playing on swings"
            ],
            "hidden_object_descriptions": ["a green picnic basket", "a red frisbee", "a blue bicycle"]
        },
        {
            "name": "Forest",
            "scene_descriptions": [
                "a dense forest with towering trees, winding trails, and shafts of sunlight piercing through the canopy",
                "a misty morning in the forest with dew-covered foliage and wildlife awakening",
                "an autumn forest scene with colorful fallen leaves, a carpet of moss, and a tranquil stream"
            ],
            "hidden_object_descriptions": ["a wooden lantern", "a red backpack", "a silver compass"]
        },
        {
            "name": "Desert",
            "scene_descriptions": [
                "a vast desert landscape with rolling sand dunes, a clear blue sky, and a solitary cactus",
                "a desert oasis with palm trees surrounding a sparkling water pool under the midday sun",
                "a twilight desert scene with vibrant sunsets, shadows stretching over the sand, and distant rocky formations"
            ],
            "hidden_object_descriptions": ["a golden hourglass", "a blue scarf", "a mirage image"]
        },
        {
            "name": "Cityscape",
            "scene_descriptions": [
                "a bustling city skyline at night with illuminated skyscrapers and busy streets below",
                "a vibrant downtown area during the day with pedestrians, storefronts, and traffic",
                "a panoramic city view from a high vantage point overlooking parks, rivers, and urban buildings"
            ],
            "hidden_object_descriptions": ["a yellow taxi", "a green traffic light", "a red rooftop antenna"]
        },
        {
            "name": "Mountains",
            "scene_descriptions": [
                "a majestic mountain range with snow-capped peaks, evergreen forests, and clear alpine lakes",
                "a serene mountain valley with wildflowers, a meandering river, and hikers exploring the trails",
                "a rugged mountain terrain with rocky cliffs, cascading waterfalls, and dense fog"
            ],
            "hidden_object_descriptions": ["a brown hiking boot", "a blue binoculars", "a white climbing rope"]
        },
        {
            "name": "Museum",
            "scene_descriptions": [
                "a grand museum hall with towering pillars, art exhibits, and visitors admiring the displays",
                "an ancient artifacts gallery featuring sculptures, pottery, and historical relics under soft lighting",
                "a modern art museum interior with abstract installations, bright colors, and interactive exhibits"
            ],
            "hidden_object_descriptions": ["a golden statue replica", "a red exhibit plaque", "a magnifying glass"]
        },
        {
            "name": "Halloween Party",
            "scene_descriptions": [
                "a spooky Halloween party with decorated pumpkins, cobwebs, and guests in creative costumes",
                "a haunted house themed party with eerie lighting, ghost decorations, and eerie music playing",
                "a backyard Halloween gathering with a bonfire, jack-o'-lanterns, and trick-or-treaters roaming around"
            ],
            "hidden_object_descriptions": ["a black witch hat", "a spooky mask", "a glowing skeleton key"]
        },
        {
            "name": "Space Station",
            "scene_descriptions": [
                "the interior of a futuristic space station with control panels, large windows overlooking Earth, and astronauts floating",
                "a space station docking bay with spacecraft arrivals, maintenance robots, and high-tech equipment",
                "a command center inside the space station bustling with scientists monitoring space missions"
            ],
            "hidden_object_descriptions": ["a silver space helmet", "a blue communication device", "a red tool kit"]
        },
        {
            "name": "Carnival",
            "scene_descriptions": [
                "a vibrant carnival with colorful tents, rides spinning under bright lights, and crowds enjoying games",
                "a nighttime carnival scene with illuminated Ferris wheels, food stalls, and performers entertaining the audience",
                "a day-time carnival filled with laughter, cotton candy stands, and funfair attractions"
            ],
            "hidden_object_descriptions": ["a striped balloon", "a red ticket stub", "a clown nose"]
        },
        {
            "name": "Underwater Reef",
            "scene_descriptions": [
                "a lively underwater reef with colorful corals, diverse marine life, and sunlight filtering through the water",
                "a serene underwater scene featuring a variety of fish, sea turtles, and swaying sea anemones",
                "an active reef environment with schools of fish, vibrant sponges, and hidden caves"
            ],
            "hidden_object_descriptions": ["a blue starfish", "a yellow seashell", "a green seaweed strand"]
        },
        {
            "name": "Farm",
            "scene_descriptions": [
                "a traditional farm landscape with a red barn, grazing livestock, and expansive green fields",
                "a busy farm scene with tractors plowing, farmers tending to crops, and a harvest in progress",
                "a cozy farmyard setting with a white farmhouse, vegetable gardens, and chickens roaming around"
            ],
            "hidden_object_descriptions": ["a straw hat", "a wooden pitchfork", "a red tractor toy"]
        },
        {
            "name": "Snowy Landscape",
            "scene_descriptions": [
                "a tranquil snowy village with frost-covered rooftops, evergreen trees, and gently falling snowflakes",
                "a winter wonderland scene featuring ice-covered lakes, snowdrifts, and people skiing down slopes",
                "a serene snowy forest with pine trees blanketed in white, animal tracks, and a frozen river"
            ],
            "hidden_object_descriptions": ["a blue mitten", "a red sled", "a white snowflake ornament"]
        },
        {
            "name": "Street Market",
            "scene_descriptions": [
                "a bustling street market with vibrant stalls, assorted goods, and shoppers browsing the items",
                "a lively night market illuminated by string lights, food vendors serving delicacies, and street performers entertaining",
                "a colorful daytime market scene with fresh produce stands, handmade crafts, and busy vendors"
            ],
            "hidden_object_descriptions": ["a green fruit basket", "a red scarf", "a lantern"]
        },
        {
            "name": "Medieval Castle",
            "scene_descriptions": [
                "a grand medieval castle perched on a hill with stone towers, battlements, and a surrounding moat",
                "an interior of a medieval castle hall with long wooden tables, banners hanging from the walls, and knights in armor",
                "a castle courtyard featuring a stone archway, garden pathways, and horses tied near the stable"
            ],
            "hidden_object_descriptions": ["a golden crown", "a silver shield", "a sword replica"]
        },
        {
            "name": "Soccer Field",
            "scene_descriptions": [
                "a vibrant soccer field during a match with players in action, cheering crowds, and goalposts",
                "a sunny day at the soccer field with kids practicing, coaches instructing, and grass freshly cut",
                "an evening soccer game illuminated by stadium lights with intense gameplay and enthusiastic spectators"
            ],
            "hidden_object_descriptions": ["a white soccer ball", "a red team jersey", "a yellow whistle"]
        },
        {
            "name": "School Classroom",
            "scene_descriptions": [
                "a lively school classroom with students seated at desks, a blackboard filled with lessons, and educational posters",
                "a quiet classroom setting with bookshelves, a teacher assisting a student, and artwork displayed on the walls",
                "a modern classroom equipped with computers, interactive boards, and collaborative workspaces"
            ],
            "hidden_object_descriptions": ["a blue pencil", "a green apple", "a globe"]
        },
        {
            "name": "Airport",
            "scene_descriptions": [
                "a busy airport terminal with passengers checking in, flights arriving and departing, and luggage conveyors",
                "an airplane on the runway preparing for takeoff with ground staff attending to it under a clear sky",
                "the interior of an airport lounge featuring seating areas, departure boards, and travelers waiting for their flights"
            ],
            "hidden_object_descriptions": ["a red suitcase", "a blue passport holder", "a white boarding pass"]
        },
        {
            "name": "Restaurant Kitchen",
            "scene_descriptions": [
                "a bustling restaurant kitchen with chefs cooking, sizzling pans, and ingredients being prepared",
                "a clean and organized kitchen environment with countertops filled with fresh produce and utensils",
                "a busy evening kitchen scene with orders being shouted, dishes being plated, and flames from the stove"
            ],
            "hidden_object_descriptions": ["a stainless steel spoon", "a red apron", "a chef's hat"]
        },
        {
            "name": "Subway Station",
            "scene_descriptions": [
                "a crowded subway station with trains arriving and departing, passengers rushing to platforms, and digital displays",
                "an underground subway platform featuring tiled walls, waiting benches, and advertisements overhead",
                "a nighttime subway station scene with illuminated signs, quiet corners, and the distant sound of trains"
            ],
            "hidden_object_descriptions": ["a yellow ticket", "a blue map", "a subway token"]
        },
        {
            "name": "Amusement Park",
            "scene_descriptions": [
                "a lively amusement park with roller coasters, ferris wheels, and brightly lit attractions",
                "a sunny day at the amusement park featuring game booths, cotton candy stands, and joyful visitors",
                "a nighttime amusement park scene with colorful lights, bustling rides, and entertaining performances"
            ],
            "hidden_object_descriptions": ["a red balloon", "a green ticket stub", "a plush toy"]
        },
        {
            "name": "Hospital",
            "scene_descriptions": [
                "a modern hospital lobby with reception desks, waiting areas, and medical staff attending to patients",
                "a busy hospital emergency room featuring doctors examining patients, medical equipment, and urgent care activities",
                "a quiet hospital ward with patient beds, nurses assisting, and soothing decor for recovery"
            ],
            "hidden_object_descriptions": ["a blue stethoscope", "a white nurse cap", "a medicine bottle"]
        },
        {
            "name": "Library",
            "scene_descriptions": [
                "a cozy library interior with tall bookshelves, reading tables, and individuals engrossed in books",
                "a quiet study area within the library featuring computers, study lamps, and comfortable seating",
                "a large library hall with section signs, ticking clocks, and patrons searching for literature"
            ],
            "hidden_object_descriptions": ["a green bookmark", "a red library card", "a reading lamp"]
        },
        {
            "name": "Zoo",
            "scene_descriptions": [
                "a vibrant zoo environment with various animal enclosures, visitors observing wildlife, and informational signs",
                "a sunny day at the zoo featuring elephants bathing, monkeys swinging, and children feeding giraffes",
                "an evening zoo scene with lit pathways, nocturnal animals waking up, and families enjoying the exhibits"
            ],
            "hidden_object_descriptions": ["a blue animal hat", "a red feeding tray", "binoculars"]
        },
        {
            "name": "Concert Hall",
            "scene_descriptions": [
                "a grand concert hall filled with an orchestra, a captivated audience, and elegant stage lighting",
                "a lively concert scene with musicians performing on stage, speakers amplifying sound, and fans cheering",
                "an indoor concert setting featuring a band playing instruments, colorful light effects, and enthusiastic attendees"
            ],
            "hidden_object_descriptions": ["a yellow microphone", "a silver guitar pick", "a drumstick"]
        },
        {
            "name": "Bakery",
            "scene_descriptions": [
                "a charming bakery display with assorted breads, pastries, and sweet treats arranged on shelves",
                "a busy bakery kitchen where bakers are mixing dough, decorating cakes, and preparing fresh goods",
                "a cozy bakery storefront featuring a glass window displaying delicious baked items and welcoming signage"
            ],
            "hidden_object_descriptions": ["a red rolling pin", "a blue cupcake liner", "a baker's hat"]
        },
        {
            "name": "Fire Station",
            "scene_descriptions": [
                "a bustling fire station with firefighters preparing equipment, fire trucks parked outside, and training drills",
                "the interior of a fire station featuring a living area, gear storage, and a briefing room",
                "a scene outside the fire station with firefighters responding to an emergency call and hoses being loaded"
            ],
            "hidden_object_descriptions": ["a yellow helmet", "a red fire hose", "a fire extinguisher"]
        },
        {
            "name": "Art Studio",
            "scene_descriptions": [
                "a creative art studio filled with canvases, paint supplies, and artists working on their masterpieces",
                "an organized art space with easels set up, colorful palettes, and inspirational artwork adorning the walls",
                "a lively art workshop scene featuring sculptors shaping materials, painters blending colors, and students learning techniques"
            ],
            "hidden_object_descriptions": ["a blue paintbrush", "a red sketchpad", "a palette knife"]
        },
        {
            "name": "Train Station",
            "scene_descriptions": [
                "a historic train station with steam engines, platform tracks, and passengers boarding trains",
                "a busy modern train station featuring high-speed trains, electronic departure boards, and bustling crowds",
                "an early morning train station scene with misty platforms, waiting passengers, and the first train arriving"
            ],
            "hidden_object_descriptions": ["a green train ticket", "a yellow luggage tag", "a conductor's hat"]
        },
        {
            "name": "Space Observatory",
            "scene_descriptions": [
                "an advanced space observatory with large telescopes, star maps, and scientists analyzing data",
                "the exterior of a space observatory perched on a mountain, under a night sky filled with stars",
                "an interior view of a space observatory's control room with intricate instruments and glowing screens"
            ],
            "hidden_object_descriptions": ["a telescope lens", "a star chart", "a space map"]
        },
        {
            "name": "Boat Harbor",
            "scene_descriptions": [
                "a bustling boat harbor with various vessels docked, fishermen mending nets, and seagulls soaring above",
                "a serene boat harbor at dawn with mist rising from the water and boats gently rocking",
                "an active boat harbor scene with sailboats setting sail, ferries arriving, and harbor workers coordinating traffic"
            ],
            "hidden_object_descriptions": ["a captain's hat", "a fishing rod", "a lifebuoy"]
        },
        {
            "name": "Ancient Ruins",
            "scene_descriptions": [
                "ancient ruins with crumbling stone structures, overgrown vines, and mysterious carvings",
                "a deserted ancient temple nestled in a jungle, with statues guarding the entrance",
                "the remnants of an old civilization with broken pillars, stone pathways, and hidden chambers"
            ],
            "hidden_object_descriptions": ["a stone tablet", "an ancient amulet", "a broken sword"]
        },
        {
            "name": "Pirate Ship",
            "scene_descriptions": [
                "a grand pirate ship sailing the high seas with billowing sails, cannons ready, and pirates aboard",
                "the deck of a pirate ship under a starlit sky, with crew members navigating and swabbing the deck",
                "a pirate ship anchored near a treasure island, with pirates searching for hidden loot"
            ],
            "hidden_object_descriptions": ["a pirate hat", "a treasure map", "a cutlass"]
        },
        {
            "name": "Volcano",
            "scene_descriptions": [
                "a dramatic volcanic landscape with smoking craters, flowing lava, and rugged terrain",
                "a volcano erupting at dusk with fiery lava streams illuminating the sky",
                "the base of a towering volcano surrounded by lava rocks, ash clouds, and volcanic flora"
            ],
            "hidden_object_descriptions": ["a lava rock", "a volcanic crystal", "a charred log"]
        },
        {
            "name": "Ancient Library",
            "scene_descriptions": [
                "an ancient library filled with tall bookshelves, dusty tomes, and intricate wooden ladders",
                "a secluded room within an ancient library with scrolls, candles, and mysterious artifacts",
                "the grand hall of an ancient library with stained glass windows, ornate decorations, and scholars studying"
            ],
            "hidden_object_descriptions": ["a scroll", "an old key", "a quill pen"]
        },
        {
            "name": "Robot Factory",
            "scene_descriptions": [
                "a high-tech robot factory with assembly lines, robotic arms, and engineers monitoring production",
                "the interior of a robot factory featuring various robots in different stages of assembly",
                "a futuristic robot factory floor with conveyor belts, automated systems, and testing stations"
            ],
            "hidden_object_descriptions": ["a circuit board", "a gear", "a robot hand"]
        },
        {
            "name": "Ancient Battlefield",
            "scene_descriptions": [
                "an ancient battlefield with worn trenches, scattered weapons, and remnants of armor",
                "a historic battlefield scene with silhouettes of warriors, broken shields, and abandoned weapons",
                "the aftermath of an ancient battle with smoke rising, debris scattered, and memorials marking the ground"
            ],
            "hidden_object_descriptions": ["a helmet", "a sword", "a shield"]
        },
        {
            "name": "Fairy Garden",
            "scene_descriptions": [
                "a magical fairy garden with tiny houses, glowing flowers, and fluttering wings",
                "a whimsical fairy garden scene with sparkling streams, enchanted trees, and fairy lights",
                "a hidden fairy garden with miniature bridges, colorful mushrooms, and mystical pathways"
            ],
            "hidden_object_descriptions": ["a fairy wand", "a glowing flower", "a tiny lantern"]
        },
        {
            "name": "Western Town",
            "scene_descriptions": [
                "a rustic western town with wooden saloons, horse-drawn carriages, and dusty streets",
                "the main street of a western town during a sunset with cowboys riding and shops bustling",
                "a deserted western town with boarded-up buildings, tumbleweeds rolling by, and a lone sheriff's office"
            ],
            "hidden_object_descriptions": ["a cowboy hat", "a revolver", "a wanted poster"]
        },
        {
            "name": "Haunted Forest",
            "scene_descriptions": [
                "a dark haunted forest with twisted trees, eerie fog, and mysterious shadows lurking",
                "a spooky haunted forest scene with ghostly apparitions, gnarled branches, and glowing eyes",
                "an abandoned haunted forest with overgrown paths, creepy stone markers, and chilling whispers"
            ],
            "hidden_object_descriptions": ["a ghostly lantern", "a witch's broom", "a haunted mirror"]
        },
        {
            "name": "Futuristic City",
            "scene_descriptions": [
                "a sprawling futuristic city with towering skyscrapers, flying vehicles, and neon lights",
                "a high-tech futuristic cityscape at night with holographic advertisements and bustling streets",
                "an aerial view of a futuristic city with advanced architecture, green spaces, and automated transport systems"
            ],
            "hidden_object_descriptions": ["a hologram device", "a futuristic gadget", "a neon sign"]
        },
        {
            "name": "Ancient Pyramid",
            "scene_descriptions": [
                "an ancient pyramid rising from the desert with intricate carvings and towering steps",
                "the interior of an ancient pyramid with labyrinthine passages, hidden chambers, and sacred artifacts",
                "the base of an ancient pyramid surrounded by palm trees, sandy dunes, and historic statues"
            ],
            "hidden_object_descriptions": ["a pharaoh's mask", "an ancient scroll", "a golden anklet"]
        },
        {
            "name": "Wild West Ranch",
            "scene_descriptions": [
                "a bustling wild west ranch with cattle, ranch hands working, and horses grazing",
                "the main area of a wild west ranch featuring a barn, stables, and a corral",
                "a panoramic view of a wild west ranch at sunrise with expansive fields and rolling hills"
            ],
            "hidden_object_descriptions": ["a lasso", "a cowboy boot", "a feed bucket"]
        },
        {
            "name": "Mystic Cave",
            "scene_descriptions": [
                "a mysterious mystic cave with glowing crystals, underground rivers, and hidden chambers",
                "the entrance of a mystic cave surrounded by lush vegetation and ancient symbols",
                "an illuminated mystic cave interior with sparkling gemstones, eerie lights, and secret passages"
            ],
            "hidden_object_descriptions": ["a crystal shard", "an ancient key", "a glowing stone"]
        },
        {
            "name": "Futuristic Laboratory",
            "scene_descriptions": [
                "a cutting-edge futuristic laboratory with advanced equipment, holographic displays, and scientists conducting experiments",
                "the interior of a futuristic laboratory featuring robotic assistants, sleek surfaces, and high-tech instruments",
                "a bustling futuristic lab environment with interactive screens, automated machinery, and innovative research stations"
            ],
            "hidden_object_descriptions": ["a microchip", "a lab flask", "a robotic arm"]
        },
        {
            "name": "Ancient Temple",
            "scene_descriptions": [
                "an ancient temple nestled in a dense jungle with ornate pillars, statues, and sacred altars",
                "the grand entrance of an ancient temple adorned with intricate carvings and guarded by stone sentinels",
                "the serene courtyard of an ancient temple with tranquil pools, blooming flowers, and spiritual symbols"
            ],
            "hidden_object_descriptions": ["a sacred relic", "a ceremonial torch", "an ancient scroll"]
        },
        {
            "name": "Ice Palace",
            "scene_descriptions": [
                "a magnificent ice palace shimmering under the northern lights with crystalline structures and frozen fountains",
                "the grand hall of an ice palace featuring sparkling chandeliers, ice sculptures, and translucent walls",
                "an outdoor ice palace scene with glistening towers, reflective surfaces, and a snow-covered landscape"
            ],
            "hidden_object_descriptions": ["an ice crystal", "a frost-covered crown", "a snowflake pendant"]
        },
        {
            "name": "Gothic Cathedral",
            "scene_descriptions": [
                "a towering gothic cathedral with stained glass windows, flying buttresses, and intricate stone carvings",
                "the interior of a gothic cathedral featuring grand arches, ornate pews, and a majestic altar",
                "a nighttime view of a gothic cathedral illuminated by candlelight, casting long shadows and highlighting architectural details"
            ],
            "hidden_object_descriptions": ["a stained glass window", "a candlestick", "a holy book"]
        },
        {
            "name": "Ancient Marketplace",
            "scene_descriptions": [
                "an ancient marketplace bustling with vendors, colorful stalls, and diverse goods",
                "the vibrant scene of an ancient marketplace with traders negotiating, customers browsing, and entertainers performing",
                "a lively ancient marketplace at midday with fresh produce, handcrafted items, and a variety of aromas"
            ],
            "hidden_object_descriptions": ["a merchant's scale", "a woven basket", "a spice jar"]
        },
        {
            "name": "Steampunk Workshop",
            "scene_descriptions": [
                "a detailed steampunk workshop filled with gears, cogs, and intricate machinery",
                "the interior of a steampunk workshop featuring brass instruments, steam-powered devices, and creative inventions",
                "a bustling steampunk workshop scene with artisans crafting mechanical devices and tinkering with parts"
            ],
            "hidden_object_descriptions": ["a gear wheel", "a steam valve", "a brass key"]
        },
        {
            "name": "Enchanted Forest",
            "scene_descriptions": [
                "an enchanted forest with magical creatures, glowing plants, and mystical pathways",
                "a twilight scene in an enchanted forest with shimmering lights, fairy houses, and mythical beings",
                "the heart of an enchanted forest featuring an ancient tree, sparkling streams, and enchanted flora"
            ],
            "hidden_object_descriptions": ["a magic wand", "a fairy dust pouch", "a glowing orb"]
        },
        {
            "name": "Pirate Cove",
            "scene_descriptions": [
                "a hidden pirate cove with anchored ships, treasure chests, and pirate flags flying high",
                "the bustling pirate cove scene with pirates loading goods, repairing ships, and searching for treasure",
                "a serene pirate cove at sunset with calm waters, palm trees, and a bonfire gathering"
            ],
            "hidden_object_descriptions": ["a treasure map", "a pirate flag", "a compass"]
        }
    ]

        # Define standard vocabulary based on difficulty levels
        self.standard_vocabulary = {
            "complexity_level": {
                "Easy": "simple",
                "Medium": "moderately detailed",
                "Hard": "highly intricate"
            },
            "hidden_object_size": {
                "Easy": "large",
                "Medium": "medium-sized",
                "Hard": "small"
            },
            "visibility_instructions": {
                "Easy": "clearly visible",
                "Medium": "blend in",
                "Hard": "carefully concealed"
            },
            "lighting_instructions": {
                "Easy": "bright lighting",
                "Medium": "natural lighting",
                "Hard": "subtle shadows"
            },
            "mood": {
                "Easy": "cheerful",
                "Medium": "lively",
                "Hard": "mysterious"
            },
            "desired_interaction": {
                "Easy": "easily find the object",
                "Medium": "explore the scene",
                "Hard": "carefully search"
            }
        }

    async def generate_prompt(self, rating: int) -> Optional[Dict[str, str]]:
        """
        Generate a structured prompt containing an Image Prompt and a Validation Question.

        Dynamically determines the difficulty level, selects a theme, and adjusts other prompt attributes based on the rating.

        Args:
            rating (int): Numerical rating (1-10) to determine the difficulty level.

        Returns:
            Optional[Dict[str, str]]: Dictionary with 'image_prompt' and 'validation_question' keys, or None if an error occurs.
        """
        try:
            # Randomly select a theme from the predefined list
            theme = random.choice(self.themes)
            logging.info(f"Selected Theme: {theme['name']}")

            # Randomly select scene_description and hidden_object_description from the theme
            scene_description = random.choice(theme["scene_descriptions"])
            hidden_object_description = random.choice(theme["hidden_object_descriptions"])

            # Generate a random number of hidden objects between 1 and 10
            number_of_hidden_objects = random.randint(1, 10)  # New code added
            logging.info(f"Number of Hidden Objects: {number_of_hidden_objects}")

            # Generate a PromptTemplate instance with the selected theme and provided rating
            prompt_template = PromptTemplate(
                difficulty_level="",  # Will be set dynamically based on rating
                rating=rating,
                complexity_level="",  # Will be set dynamically based on rating
                scene_description=scene_description,
                hidden_object_size="",  # Will be set based on difficulty
                hidden_object_description=hidden_object_description,
                visibility_instructions="",  # Will be set based on difficulty
                lighting_instructions="",  # Will be set based on difficulty
                mood="",  # Will be set based on difficulty
                desired_interaction="",  # Will be set based on difficulty
                number_of_hidden_objects=number_of_hidden_objects  # Assign the random number
            )

            # Determine difficulty level based on rating
            difficulty = PromptTemplate.determine_difficulty_level(rating)
            logging.info(f"Determined Difficulty: {difficulty}")

            # Assign standard vocabulary based on difficulty
            prompt_template.hidden_object_size = self.standard_vocabulary["hidden_object_size"][difficulty]
            prompt_template.visibility_instructions = self.standard_vocabulary["visibility_instructions"][difficulty]
            prompt_template.lighting_instructions = self.standard_vocabulary["lighting_instructions"][difficulty]
            prompt_template.mood = self.standard_vocabulary["mood"][difficulty]
            prompt_template.desired_interaction = self.standard_vocabulary["desired_interaction"][difficulty]

            # Generate the structured image prompt
            structured_image_prompt = prompt_template.generate_prompt()
            logging.info(f"Structured Image Prompt: {structured_image_prompt}")

            # Prepare the messages for OpenAI API, incorporating the structured prompt
            response = await self.client.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a creative AI assisting in generating prompts for an AI image generation model. "
                            "Each prompt consists of two parts: an Image Prompt and a Validation Question. "
                            "The Image Prompt should describe an image with specific attributes such as difficulty level, scene complexity, hidden object details, etc. "
                            "The Validation Question should correspond to the image prompt by asking about the presence of the hidden object. "
                            "Please provide the output in JSON format with 'image_prompt' and 'validation_question' keys."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{structured_image_prompt}\n\n"
                            "Generate a corresponding Validation Question that asks if the specific hidden item is present in the image. "
                            "Please respond in the following JSON format:\n"
                            "{\n"
                            '  "image_prompt": "Your image prompt here.",\n'
                            '  "validation_question": "Your validation question here."\n'
                            "}"
                        ),
                    },
                ],
                max_tokens=300,
            )

            content = response.choices[0].message.content.strip()
            prompt_data = parse_prompt_response(content)
            if prompt_data:
                logging.info(f"Image Prompt: {prompt_data['image_prompt']}")
                logging.info(f"Validation Question: {prompt_data['validation_question']}")
                return prompt_data
            else:
                logging.error("Failed to parse the prompt response.")
                return None
        except OpenAIError as e:
            logging.error(f"Error generating prompt: {e}")
            return None
        except ValidationError as ve:
            logging.error(f"Prompt validation failed: {ve}")
            return None

    async def generate_prompts(self, num_prompts: int) -> List[Optional[Dict[str, str]]]:
        """
        Generate multiple prompts asynchronously.

        Each prompt is assigned a random rating between 1 and 10 with an even distribution.

        Args:
            num_prompts (int): Number of prompts to generate.

        Returns:
            List[Optional[Dict[str, str]]]: List of generated prompts.
        """
        # Generate random ratings between 1 and 10 for each prompt
        ratings = [random.randint(1, 10) for _ in range(num_prompts)]
        logging.info(f"Generated Ratings: {ratings}")

        # Create asynchronous tasks for prompt generation with random ratings
        tasks = [asyncio.create_task(self.generate_prompt(rating)) for rating in ratings]
        return await asyncio.gather(*tasks)

