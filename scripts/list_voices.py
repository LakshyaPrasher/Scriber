import asyncio
import edge_tts

async def main():
    voices = await edge_tts.list_voices()
    print(f"Total voices: {len(voices)}")
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]
    print(f"English voices: {len(en_voices)}")
    for v in sorted(en_voices, key=lambda x: (x["Locale"], x["Gender"], x["ShortName"])):
        print(f"{v['ShortName']} | {v['Gender']} | {v['Locale']} | {v.get('FriendlyName', '')}")

if __name__ == "__main__":
    asyncio.run(main())
