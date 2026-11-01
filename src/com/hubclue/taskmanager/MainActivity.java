package com.hubclue.taskmanager;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Task Manager - native Android shell around the offline web app in assets/www.
 *
 * The page is served from a virtual https origin (app.taskmanager.local) that is
 * answered entirely from the APK's assets by shouldInterceptRequest(). That gives
 * the web app a real, stable, secure origin, which is what makes localStorage
 * (task/settings persistence) reliable, and it needs no INTERNET permission.
 */
public class MainActivity extends Activity {

    private static final String HOST = "app.taskmanager.local";
    private static final String START_URL = "https://" + HOST + "/index.html";
    private static final String ASSET_ROOT = "www";

    private WebView web;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);

        web = new WebView(this);
        web.setBackgroundColor(0xFF9DB4FF);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage -> app data survives restarts
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(false);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setLoadWithOverviewMode(false);
        s.setUseWideViewPort(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setJavaScriptCanOpenWindowsAutomatically(false);
        s.setCacheMode(WebSettings.LOAD_NO_CACHE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            web.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_IMPORTANT, false);
        }

        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                return serve(req.getUrl());
            }

            @Override
            @SuppressWarnings("deprecation")
            public WebResourceResponse shouldInterceptRequest(WebView view, String url) {
                return serve(Uri.parse(url));
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return openExternal(url);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                return openExternal(req.getUrl().toString());
            }
        });

        if (state == null) {
            web.loadUrl(START_URL);
        } else {
            web.restoreState(state);
        }
    }

    /** True when the URL is not ours: hand it to the system browser instead. */
    private boolean openExternal(String url) {
        if (url == null) return false;
        Uri u = Uri.parse(url);
        if (HOST.equals(u.getHost())) return false;
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
        } catch (Exception ignored) {
            // no handler installed - stay in the app
        }
        return true;
    }

    /** Resolve https://app.taskmanager.local/<path> straight out of the APK assets. */
    private WebResourceResponse serve(Uri u) {
        if (u == null || !HOST.equals(u.getHost())) return null;

        String path = u.getPath();
        if (path == null || path.length() == 0 || "/".equals(path)) path = "/index.html";
        if (path.contains("..")) path = "/index.html";

        try {
            InputStream in = getAssets().open(ASSET_ROOT + path);
            Map<String, String> headers = new HashMap<String, String>();
            headers.put("Cache-Control", "no-store");
            headers.put("Access-Control-Allow-Origin", "*");
            return new WebResourceResponse(mimeOf(path), "utf-8", 200, "OK", headers, in);
        } catch (IOException e) {
            Map<String, String> headers = new HashMap<String, String>();
            byte[] body = ("Not found: " + path).getBytes();
            return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found",
                    headers, new ByteArrayInputStream(body));
        }
    }

    private static String mimeOf(String path) {
        String p = path.toLowerCase();
        if (p.endsWith(".html") || p.endsWith(".htm")) return "text/html";
        if (p.endsWith(".js")) return "application/javascript";
        if (p.endsWith(".css")) return "text/css";
        if (p.endsWith(".json")) return "application/json";
        if (p.endsWith(".svg")) return "image/svg+xml";
        if (p.endsWith(".png")) return "image/png";
        if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
        if (p.endsWith(".webp")) return "image/webp";
        if (p.endsWith(".woff2")) return "font/woff2";
        if (p.endsWith(".woff")) return "font/woff";
        if (p.endsWith(".ttf")) return "font/ttf";
        return "text/plain";
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        web.saveState(out);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.setVisibility(View.GONE);
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
