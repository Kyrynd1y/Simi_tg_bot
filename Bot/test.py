import dotenv
import os
import replicate

dotenv.load_dotenv()
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')


output = replicate.run(
    "ai-forever/kandinsky-2:601eea49d49003e6ea75a11527209c4f510a93e2112c969d548fbb45b9c4f19f",
    input={"prompt": f"{input()}, 4k photo"}
)
print(output)