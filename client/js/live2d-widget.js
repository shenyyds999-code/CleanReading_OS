(function () {
    var MODEL_URL = 'https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/model.json';

    var tips = [
        '今天想看什么书？',
        '要记得还书哟~',
        '答题闯关能拿称号！',
        '借书别超时哦~',
        '欢迎来到图书馆！',
        '点击我可以互动~',
        '雷姆在这陪着你呢！',
        '注意信誉分哦~'
    ];

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
        c.style.cssText = 'position:fixed;right:10px;bottom:5px;width:180px;z-index:9998;';
        c.innerHTML = '<img src="https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/remu2048/texture_00.png" style="width:100%;opacity:0.9;cursor:pointer;" onerror="this.parentElement.remove()" onclick="var t=document.getElementById(\'live2d-tip\');if(!t)return;t.textContent=\'' + tips[Math.floor(Math.random() * tips.length)] + '\';t.style.opacity=\'1\';setTimeout(function(){t.style.opacity=\'0\'},4000);">';
        document.body.appendChild(c);

        var tip = document.getElementById('live2d-tip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'live2d-tip';
            tip.style.cssText = 'position:fixed;right:30px;bottom:280px;max-width:200px;padding:10px 14px;background:rgba(54,59,63,0.92);color:#e0e0e0;border-radius:14px 14px 4px 14px;font-size:13px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #4a5056;';
            document.body.appendChild(tip);
        }
    }

    var tipBox = document.getElementById('live2d-tip');
    if (!tipBox) {
        tipBox = document.createElement('div');
        tipBox.id = 'live2d-tip';
        tipBox.style.cssText = 'position:fixed;right:30px;bottom:280px;max-width:200px;padding:10px 14px;background:rgba(54,59,63,0.92);color:#e0e0e0;border-radius:14px 14px 4px 14px;font-size:13px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #4a5056;';
        document.body.appendChild(tipBox);
    }

    function showTip() {
        tipBox.textContent = tips[Math.floor(Math.random() * tips.length)];
        tipBox.style.opacity = '1';
        setTimeout(function () { tipBox.style.opacity = '0'; }, 4000);
    }

    if (typeof L2Dwidget !== 'undefined') {
        initWidget();
    } else {
        loadScript('https://cdn.jsdelivr.net/npm/live2d-widget@3.0.5/lib/L2Dwidget.min.js', initWidget);
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
                        'every idle 60s': tips,
                        'tap body': tips,
                        'tap face': ['呀！不要戳脸啦~', '呜...被戳了...'],
                        'mouseover': [
                            { text: '雷姆来帮你了！', timeout: 3000 }
                        ]
                    }
                }
            });

            document.getElementById('live2d-widget')?.style?.setProperty?.('z-index', '9998');
        } catch (e) {
            console.warn('Live2D: L2Dwidget init failed', e.message);
            showFallback();
        }
    }

    setInterval(showTip, 30000);
})();
