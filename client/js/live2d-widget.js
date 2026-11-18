(function () {
    var MODEL_URL = 'https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/model.json';

    var tips = [
        '今天想看什么书？~',
        '要记得还书哟~',
        '答题闯关能拿称号呢！',
        '借书别超时哦~',
        '欢迎来到图书馆！',
        '雷姆会一直陪着你哟~',
        '注意信誉分哦~',
        '捐书可以加信誉分呢~',
        '有问题可以找管理员哦~',
        '祝你阅读愉快！'
    ];

    var isHidden = localStorage.getItem('live2d-hidden') === 'true';

    function loadScript(src, cb) {
        var s = document.createElement('script');
        s.src = src;
        s.onload = cb;
        s.onerror = function () {
            showFallback();
        };
        document.head.appendChild(s);
    }

    function showFallback() {
        if (document.getElementById('live2d-container')) return;
        var c = document.createElement('div');
        c.id = 'live2d-container';
        c.style.cssText = 'position:fixed;right:10px;bottom:100px;width:180px;z-index:999;';
        c.innerHTML = '<img src="https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/remu2048/texture_00.png" style="width:100%;opacity:0.9;cursor:pointer;" onerror="this.parentElement.remove()">';
        document.body.appendChild(c);

        var tip = document.getElementById('live2d-tip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'live2d-tip';
            tip.style.cssText = 'position:fixed;right:30px;bottom:320px;max-width:200px;padding:10px 14px;background:rgba(255,255,255,0.96);color:#1b1622;border-radius:14px 14px 4px 14px;font-size:13px;z-index:1000;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #dfe2ea;box-shadow:0 4px 14px rgba(27,22,34,0.10);';
            document.body.appendChild(tip);
        }

        createToggleButton();
    }

    var tipBox = document.getElementById('live2d-tip');
    if (!tipBox) {
        tipBox = document.createElement('div');
        tipBox.id = 'live2d-tip';
        tipBox.style.cssText = 'position:fixed;right:30px;bottom:320px;max-width:200px;padding:10px 14px;background:rgba(255,255,255,0.96);color:#1b1622;border-radius:14px 14px 4px 14px;font-size:13px;z-index:1000;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #dfe2ea;box-shadow:0 4px 14px rgba(27,22,34,0.10);';
        document.body.appendChild(tipBox);
    }

    function showTip(text) {
        tipBox.textContent = text || tips[Math.floor(Math.random() * tips.length)];
        tipBox.style.opacity = '1';
        setTimeout(function () { tipBox.style.opacity = '0'; }, 4000);
    }

    function createToggleButton() {
        if (document.getElementById('live2d-toggle')) return;
        
        var btn = document.createElement('button');
        btn.id = 'live2d-toggle';
        btn.innerHTML = isHidden ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        btn.style.cssText = 'position:fixed;right:10px;bottom:320px;width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.96);border:1px solid #dfe2ea;color:#5f5a66;cursor:pointer;z-index:1001;display:flex;align-items:center;justify-content:center;font-size:14px;transition:all .2s;opacity:0.7;box-shadow:0 2px 8px rgba(27,22,34,0.10);';
        btn.onmouseover = function() { btn.style.opacity = '1'; };
        btn.onmouseout = function() { btn.style.opacity = '0.7'; };
        btn.onclick = toggleLive2d;
        document.body.appendChild(btn);
    }

    function toggleLive2d() {
        isHidden = !isHidden;
        localStorage.setItem('live2d-hidden', isHidden);
        
        var widget = document.getElementById('live2d-widget');
        var container = document.getElementById('live2d-container');
        var btn = document.getElementById('live2d-toggle');
        
        if (widget) widget.style.display = isHidden ? 'none' : 'block';
        if (container) container.style.display = isHidden ? 'none' : 'block';
        if (btn) btn.innerHTML = isHidden ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
    }

    function initWidget() {
        if (typeof L2Dwidget === 'undefined') {
            showFallback();
            return;
        }

        try {
            L2Dwidget.init({
                model: {
                    jsonPath: MODEL_URL,
                    scale: 1
                },
                display: {
                    superSample: 2,
                    width: 200,
                    height: 320,
                    position: 'right',
                    hOffset: 0,
                    vOffset: -10
                },
                mobile: {
                    show: false
                },
                react: {
                    opacityDefault: 0.8,
                    opacityOnHover: 0.4
                },
                dialog: {
                    enable: true,
                    script: {
                        'every idle 10s': tips,
                        'tap body': tips,
                        'tap face': ['呀！不要戳脸啦~', '呜...被戳了...'],
                        'mouseover': [
                            { text: '雷姆来帮你了！', timeout: 3000 }
                        ]
                    }
                }
            });

            document.getElementById('live2d-widget')?.style?.setProperty?.('z-index', '999');
            
            createToggleButton();
            
            if (isHidden) {
                var widget = document.getElementById('live2d-widget');
                if (widget) widget.style.display = 'none';
            }
        } catch (e) {
            console.warn('Live2D: L2Dwidget init failed', e.message);
            showFallback();
        }
    }

    if (typeof L2Dwidget !== 'undefined') {
        initWidget();
    } else {
        loadScript('https://cdn.jsdelivr.net/npm/live2d-widget@3.0.5/lib/L2Dwidget.min.js', initWidget);
    }

    setInterval(showTip, 15000);
})();