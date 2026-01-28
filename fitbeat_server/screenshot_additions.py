# ═══════════════════════════════════════════════════════════════
# SCREENSHOT GENERATION FOR WHATSAPP SHARING
# Add these to your server.py
# ═══════════════════════════════════════════════════════════════

# 1. Add to imports at top of server.py:
"""
from playwright.async_api import async_playwright
import base64
"""

# 2. Add to requirements.txt:
"""
playwright==1.40.0
"""

# 3. After deploying, run this command once on Railway:
"""
playwright install chromium
"""

# 4. Add this endpoint to server.py (before app.include_router):

@api_router.get("/u/{user_id}/workout/{workout_id}/image")
async def generate_workout_image(user_id: str, workout_id: str, lang: int = 0):
    """Generate PNG screenshot of workout for WhatsApp sharing"""
    from fastapi.responses import Response
    
    # Get workout data
    workout = await db.workouts.find_one(
        {"id": workout_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not workout:
        return JSONResponse(status_code=404, content={"error": "Workout not found"})
    
    # Generate the HTML
    html_content = generate_workout_html(workout, user_id, lang)
    
    # Take screenshot using Playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.new_page(viewport={'width': 480, 'height': 800})
            
            # Load HTML content
            await page.set_content(html_content, wait_until='networkidle')
            
            # Wait for map to load (if present)
            await page.wait_for_timeout(2000)
            
            # Take screenshot
            screenshot = await page.screenshot(
                type='png',
                full_page=False,
                clip={'x': 0, 'y': 0, 'width': 480, 'height': 800}
            )
            
            await browser.close()
            
            return Response(
                content=screenshot,
                media_type="image/png",
                headers={
                    "Content-Disposition": f"attachment; filename=fitbeat_workout_{workout_id}.png",
                    "Cache-Control": "no-cache"
                }
            )
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# 5. Update the share button in generate_workout_html function
# Find this line:
#     share_text = f"...
# And replace the WhatsApp button with:

SHARE_BUTTON_HTML = '''
<!-- Download Image Button -->
<a href="/api/u/{user_id}/workout/{workout_id}/image?lang={lang}" 
   download="fitbeat_workout.png" 
   class="share-btn" 
   style="background: linear-gradient(90deg, #00d4ff 0%, #0099bb 100%); margin-bottom: 0.5rem;">
    📷 {download_image_text}
</a>

<!-- Then share on WhatsApp -->
<a href="https://wa.me/?text={share_text}" 
   target="_blank" 
   class="share-btn">
    📤 {share_whatsapp_text}
</a>

<p style="color:#666; font-size:0.75rem; text-align:center; margin-top:0.5rem;">
    {tip_text}
</p>
'''

# Translation keys to add to TRANSLATIONS dict:
EXTRA_TRANSLATIONS = {
    "download_image": ["Download Image", "הורד תמונה", "Descargar Imagen", "Télécharger Image", "Bild herunterladen", "下载图片"],
    "share_tip": ["Download the image, then share it on WhatsApp!", "הורד את התמונה ואז שתף אותה בווטסאפ!", "Descarga la imagen y compártela en WhatsApp!", "Téléchargez l'image puis partagez-la sur WhatsApp!", "Lade das Bild herunter und teile es auf WhatsApp!", "下载图片，然后在WhatsApp上分享！"],
}
