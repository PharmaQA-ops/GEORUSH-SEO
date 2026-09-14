
import webview

LIVE_URL = "https://pharmaqa-ops.github.io/GEORUSH-SEO/"

def main():
    webview.create_window(
        "GEORUSH SEO",
        LIVE_URL,
        width=1440,
        height=900,
        min_size=(1100, 700),
        resizable=True,
        background_color="#0b1118",
        text_select=True
    )
    webview.start()

if __name__ == "__main__":
    main()
