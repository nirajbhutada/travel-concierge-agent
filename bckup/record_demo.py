import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def record_demo():
    print("Starting Playwright demo recording...")
    target_url = "https://travel-concierge-frontend-4094884724.us-east1.run.app"
    record_dir = "/config/Desktop/Session1/travel-concierge-agent/recordings"
    os.makedirs(record_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/usr/bin/google-chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=record_dir,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"Navigating to {target_url}...")
        await page.goto(target_url, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Click prompt button for Kyoto itinerary
        print("Clicking example prompt button '🌸 Plan a trip to Kyoto'...")
        prompt_btn = page.locator(".prompt-btn", has_text="Plan a trip to Kyoto")
        if await prompt_btn.count() > 0:
            await prompt_btn.first.click()
        else:
            await page.fill("#input", "Plan a 3-day trip to Kyoto, Japan")
            await page.click("button.send-btn")

        # Wait for agent response
        print("Waiting for itinerary response...")
        await page.wait_for_timeout(10000)

        # 2. Type second richer prompt: generate a postcard image & database lookup
        print("Sending second prompt (Image generation & tool call)...")
        input_box = page.locator("#input")
        await input_box.fill("Generate a postcard image of a Kyoto temple with cherry blossoms, and search destinations in Japan")
        await page.wait_for_timeout(1000)
        await page.click("button.send-btn")

        # Wait for second response (image generation tool + search tool)
        print("Waiting for postcard image & tool call response...")
        await page.wait_for_timeout(18000)

        # Pause to showcase final results in video
        print("Final showcase delay...")
        await page.wait_for_timeout(4000)

        video_path = await page.video.path()
        print(f"Recorded video saved to: {video_path}")

        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(record_demo())
