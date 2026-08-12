package com.generated.webview;

import android.app.Activity;
import android.content.pm.ActivityInfo;
import android.graphics.Bitmap;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * {{APP_NAME}} — WebView 壳主 Activity
 * 由 WebView 生成器自动生成，请勿手动修改。
 *
 * KIOSK_MODE = true 时启用借书机模式：
 *   - 全屏沉浸
 *   - 锁定竖屏/横屏
 *   - 禁止回退手势 / 禁止长按选中
 *   - 禁用软键盘弹出（配合扫码枪）
 *   - 保持屏幕长亮（防休眠）
 */
public class MainActivity extends Activity {

    private static final String SERVER_URL = "{{SERVER_URL}}";
    private static final boolean KIOSK_MODE = {{KIOSK_MODE}};
    private static final String APP_NAME = "{{APP_NAME}}";

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Kiosk 模式：全屏 + 屏幕常亮
        if (KIOSK_MODE) {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        }

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);          // 本地存储 (JWT/Cookie 持久化)
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setAllowFileAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(true);

        // 借书机模式：关闭缩放与长按
        if (KIOSK_MODE) {
            settings.setSupportZoom(false);
            settings.setTextZoom(100);
            webView.setOnLongClickListener(v -> true); // 禁止长按选中/复制
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    if (KIOSK_MODE) {
                        view.loadUrl(url);       // Kiosk 模式全部在壳内打开
                    } else {
                        // 非 Kiosk：站内地址壳内打开，外部链接交系统浏览器
                        if (url.startsWith(SERVER_URL)) {
                            view.loadUrl(url);
                        } else {
                            try {
                                android.content.Intent i = new android.content.Intent(
                                        android.content.Intent.ACTION_VIEW,
                                        android.net.Uri.parse(url));
                                startActivity(i);
                            } catch (Exception ignored) {
                                view.loadUrl(url);
                            }
                        }
                    }
                    return true;
                }
                return false;
            }

            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
            }
        });

        webView.setWebChromeClient(new WebChromeClient());

        // 禁用系统软键盘弹出（借书机配合扫码枪，使用 inputmode=none 的页面）
        if (KIOSK_MODE) {
            getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);
        }

        webView.loadUrl(SERVER_URL);
    }

    @Override
    public void onBackPressed() {
        if (KIOSK_MODE) {
            // 借书机：禁止返回退出到桌面
            return;
        }
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (KIOSK_MODE) {
            // 重新进入时恢复全屏
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);
        }
    }
}
