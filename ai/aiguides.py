import os 
from dotenv import load_dotenv
from openai import OpenAI

# testing purposes only!
# topic is what guide needs to be generated (ex. isolating x algebra I), i will also push a flask instance
# lang is what langauge to respond in (ex. english)

#to do, it uses latex NO MATTER WHAT!!! i need to fix the prompt
#i need to make it use bullet points
# make sure it knows that its purely education (i asked it about csgo and it tried to use math to explain csgo)

topic = "polynomial functions algebra 2"
lang = "english"

# do NOT push the env to prod tsk tsk
load_dotenv(".env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# prompt file is prompt.txt kept in same directory as ai
prompt = open("prompt.txt", "r", encoding="utf-8").read()

# gen_guide is what actually returns a string. just use gen_guide()
def gen_guide(topic, lang):
    given_prompt = f"{prompt}\nTopic: {topic}\nLanguage: {lang}"
    output = client.chat.completions.create(
        model = "gpt-5-mini",
        messages=[
            {"role": "system", "content": "You are a highly educated individual who will write educational guides for users based on their prompts."},
            {"role": "user", "content": given_prompt}
        ],
        temperature=1
    )
    return output.choices[0].message.content.strip()

def main():
        print("Generating.....")
        guide_output = gen_guide(topic, lang)
        print("\n" + guide_output + "\n")

if __name__ == "__main__":
    main()