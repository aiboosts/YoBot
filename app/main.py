
from fastapi import FastAPI, HTTPException
import os
from meme_generator import create_meme
from analyzer import load_trivy_report, analyze_logs
from discord_webhook import DiscordWebhook, DiscordEmbed
import aiohttp
import logging

# Logging-Konfiguration
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Discord Webhook URL (set in .env file)
# DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/1358542446031798624/S-90hr030GtqcMqfWg6rr5YWlQO7qVcZHK0RyvyyQUDq6Y6r54lliQ8XpEoLsmgdEtTi'

@app.post("/analyze_trivy_logs/")
async def analyze_trivy_logs():
    try:
        # Load the Trivy scan result (generated by GitHub Actions)
        trivy_report = load_trivy_report("trivy_output.json")
        logging.debug(f"Trivy Report: {trivy_report}")

        # Analyze logs (you can customize this further)
        results = analyze_logs(trivy_report)
        logging.debug(f"Analysis Results: {results}")

        # Generate meme based on vulnerability severity
        meme_path = create_meme(results['vuln_name'], results['severity'])
        logging.debug(f"Meme Path: {meme_path}")

        # Send Discord notification with meme
        await send_discord_notification(meme_path, results)

        return {"message": "Logs analyzed and meme created!"}

    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# Asynchronous Discord notification with meme
async def send_discord_notification(meme_path, results):
    try:
        if DISCORD_WEBHOOK_URL is None:
            logging.error("Discord Webhook URL is not set.")
            raise HTTPException(status_code=500, detail="Discord Webhook URL is not set.")
        
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(title="Vulnerability Alert!", description="Check out this vulnerability!", color=242424)
        embed.set_image(url=meme_path)
        embed.add_embed_field(name="Severity", value=results['severity'])
        embed.add_embed_field(name="Vulnerability", value=results['vuln_name'])
        webhook.add_embed(embed)

        # Use aiohttp for asynchronous HTTP request
        async with aiohttp.ClientSession() as session:
            response = await session.post(webhook.url, json=webhook.json())
            if response.status == 204:
                logging.info("Discord notification sent successfully!")
            else:
                logging.error(f"Failed to send Discord notification. Status code: {response.status}")
                raise HTTPException(status_code=500, detail=f"Failed to send Discord notification. Status code: {response.status}")

    except Exception as e:
        logging.error(f"Error sending Discord notification: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending Discord notification: {e}")
