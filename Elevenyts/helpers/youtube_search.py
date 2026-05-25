from youtubesearchpython import VideosSearch
import logging

# Logging ကို သတ်မှတ်ပါ (အမှားတွေ့ရင် သိအောင်)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_youtube_video(query: str) -> str or None:
    """
    ဒီ function က ပေးလိုက်တဲ့ စာသားနဲ့ ကိုက်ညီတဲ့ ပထမဆုံး YouTube video ရဲ့ URL ကို ပြန်ပေးပါတယ်။
    ဘာမှမတွေ့ရင် None ကို ပြန်ပေးပါတယ်။
    """
    try:
        logger.info(f"ရှာဖွေနေပါပြီ: '{query}'")
        # VideosSearch ကို သုံးပြီး ပထမဆုံး ၁ ခုကို ရှာပါ
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result()
        
        if result and result['result']:
            # ပထမဆုံး result ရဲ့ video ID ကို ယူပါ
            video_url = result['result'][0]['link']  # link က 'https://youtu.be/...' format နဲ့ ပြန်ပေးတယ်
            logger.info(f"တွေ့ရှိပါပြီ: {video_url}")
            return video_url
        else:
            logger.warning(f"'{query}' အတွက် ဘာမှ မတွေ့ပါဘူး။")
            return None
            
    except Exception as e:
        logger.error(f"အမှားတစ်ခု ဖြစ်သွားပါပြီ: {e}")
        return None
