(function () {
    var MODEL_URL = 'https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/model.json';

    var tips = [
        '今天想看什么书？~',
        '要记得还书哟~',
        '答题闯关能拿称号呢！',
        '借书别超时哦~',
        '欢迎来到图书馆！',
        '点击我可以互动~',
        '雷姆会一直陪着你哟~',
        '注意信誉分哦~'
    ];

    var isHidden = localStorage.getItem('live2d-hidden') === 'true';
    var currentBookTitle = '';

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
        c.innerHTML = '<img src="https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/remu2048/texture_00.png" style="width:100%;opacity:0.9;cursor:pointer;" onerror="this.parentElement.remove()" onclick="showLive2dTip();">';
        document.body.appendChild(c);

        var tip = document.getElementById('live2d-tip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'live2d-tip';
            tip.style.cssText = 'position:fixed;right:30px;bottom:280px;max-width:200px;padding:10px 14px;background:rgba(54,59,63,0.92);color:#e0e0e0;border-radius:14px 14px 4px 14px;font-size:13px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #4a5056;';
            document.body.appendChild(tip);
        }

        createChatPanel();
        createToggleButton();
    }

    var tipBox = document.getElementById('live2d-tip');
    if (!tipBox) {
        tipBox = document.createElement('div');
        tipBox.id = 'live2d-tip';
        tipBox.style.cssText = 'position:fixed;right:30px;bottom:280px;max-width:200px;padding:10px 14px;background:rgba(54,59,63,0.92);color:#e0e0e0;border-radius:14px 14px 4px 14px;font-size:13px;z-index:9999;opacity:0;transition:opacity .3s;pointer-events:none;border:1px solid #4a5056;';
        document.body.appendChild(tipBox);
    }

    function showTip(text) {
        tipBox.textContent = text || tips[Math.floor(Math.random() * tips.length)];
        tipBox.style.opacity = '1';
        setTimeout(function () { tipBox.style.opacity = '0'; }, 4000);
    }

    window.showLive2dTip = function() {
        showTip();
    };

    function setCurrentBook(title) {
        currentBookTitle = title;
    }

    window.setLive2dBook = function(title) {
        setCurrentBook(title);
    };

    function createChatPanel() {
        if (document.getElementById('live2d-chat-panel')) return;

        var panel = document.createElement('div');
        panel.id = 'live2d-chat-panel';
        panel.style.cssText = 'position:fixed;right:10px;bottom:220px;width:260px;z-index:9997;background:rgba(54,59,63,0.95);border-radius:16px;border:1px solid #4a5056;box-shadow:0 4px 20px rgba(0,0,0,0.3);display:flex;flex-direction:column;overflow:hidden;';
        
        var header = document.createElement('div');
        header.innerHTML = '<div style="padding:10px 12px;border-bottom:1px solid #4a5056;display:flex;align-items:center;gap:8px;"><img src="https://cdn.jsdelivr.net/gh/evrstr/live2d-widget-models/live2d_evrstr/rem_2/remu2048/texture_00.png" style="width:32px;height:32px;border-radius:8px;object-fit:cover;"><span style="color:#e0e0e0;font-weight:500;">雷姆</span></div>';
        panel.appendChild(header);

        var messages = document.createElement('div');
        messages.id = 'live2d-chat-messages';
        messages.style.cssText = 'height:150px;overflow-y:auto;padding:10px;scrollbar-width:thin;scrollbar-color:#4a5056 transparent;';
        messages.innerHTML = '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(255,102,153,0.15);border-radius:12px 12px 12px 4px;color:#e0e0e0;font-size:13px;">雷姆：主人~有什么想聊的吗？</div>';
        panel.appendChild(messages);

        var inputArea = document.createElement('div');
        inputArea.style.cssText = 'display:flex;gap:8px;padding:10px;border-top:1px solid #4a5056;';
        
        var input = document.createElement('input');
        input.type = 'text';
        input.id = 'live2d-chat-input';
        input.placeholder = '输入消息...';
        input.style.cssText = 'flex:1;padding:8px 12px;border:none;border-radius:20px;background:#24272a;color:#e0e0e0;font-size:13px;outline:none;';
        inputArea.appendChild(input);

        var sendBtn = document.createElement('button');
        sendBtn.innerHTML = '<i class="bi bi-send"></i>';
        sendBtn.style.cssText = 'width:36px;height:36px;border-radius:50%;background:#FF6699;border:none;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;';
        sendBtn.onclick = sendChat;
        inputArea.appendChild(sendBtn);

        var summaryBtn = document.createElement('button');
        summaryBtn.innerHTML = '<i class="bi bi-file-text"></i>';
        summaryBtn.title = '总结当前页面';
        summaryBtn.style.cssText = 'width:36px;height:36px;border-radius:50%;background:#0d6efd;border:none;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;';
        summaryBtn.onclick = summarizePage;
        inputArea.appendChild(summaryBtn);

        panel.appendChild(inputArea);

        document.body.appendChild(panel);

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChat();
            }
        });
    }

    async function sendChat() {
        var input = document.getElementById('live2d-chat-input');
        var messages = document.getElementById('live2d-chat-messages');
        var text = input.value.trim();
        
        if (!text) return;

        input.value = '';
        
        messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(33,37,41,0.8);border-radius:12px 12px 4px 12px;color:#e0e0e0;font-size:13px;text-align:right;">' + escapeHtml(text) + '</div>';
        messages.scrollTop = messages.scrollHeight;

        var sendBtn = document.querySelector('#live2d-chat-panel button:first-of-type');
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            var resp = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: JSON.stringify({
                    message: text,
                    book_title: currentBookTitle
                })
            });
            
            var data = await resp.json();
            var reply = data && data.data && data.data.reply ? data.data.reply : '雷姆有点累了呢...';
            
            messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(255,102,153,0.15);border-radius:12px 12px 12px 4px;color:#e0e0e0;font-size:13px;">雷姆：' + escapeHtml(reply) + '</div>';
            messages.scrollTop = messages.scrollHeight;
        } catch (e) {
            messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(220,53,69,0.15);border-radius:12px 12px 12px 4px;color:#ff6b6b;font-size:13px;">连接失败了呢...</div>';
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = '<i class="bi bi-send"></i>';
        }
    }

    async function summarizePage() {
        var messages = document.getElementById('live2d-chat-messages');
        var summaryBtn = document.querySelector('#live2d-chat-panel button:last-of-type');
        
        summaryBtn.disabled = true;
        summaryBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            var pageContent = extractPageContent();
            if (!pageContent) {
                messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(220,53,69,0.15);border-radius:12px 12px 12px 4px;color:#ff6b6b;font-size:13px;">当前页面没有可总结的内容呢~</div>';
                return;
            }

            messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(33,37,41,0.8);border-radius:12px 12px 4px 12px;color:#e0e0e0;font-size:13px;text-align:right;">帮我总结一下当前页面</div>';
            messages.scrollTop = messages.scrollHeight;

            var resp = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: JSON.stringify({
                    message: '请帮我总结一下当前页面内容：',
                    book_title: currentBookTitle,
                    page_content: pageContent
                })
            });
            
            var data = await resp.json();
            var reply = data && data.data && data.data.reply ? data.data.reply : '雷姆看不懂呢...';
            
            messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(255,102,153,0.15);border-radius:12px 12px 12px 4px;color:#e0e0e0;font-size:13px;">雷姆：' + escapeHtml(reply) + '</div>';
            messages.scrollTop = messages.scrollHeight;
        } catch (e) {
            messages.innerHTML += '<div style="margin-bottom:8px;padding:8px 12px;background:rgba(220,53,69,0.15);border-radius:12px 12px 12px 4px;color:#ff6b6b;font-size:13px;">连接失败了呢...</div>';
        } finally {
            summaryBtn.disabled = false;
            summaryBtn.innerHTML = '<i class="bi bi-file-text"></i>';
        }
    }

    function extractPageContent() {
        var pageContent = '';
        var path = window.location.pathname;

        if (path.includes('book.html')) {
            var title = document.querySelector('h1')?.textContent || '';
            var author = document.querySelector('#bookAuthor')?.textContent || '';
            var desc = document.querySelector('#bookDesc')?.textContent || '';
            pageContent = `书名：${title}\n作者：${author}\n简介：${desc}`;
        } else if (path.includes('index.html')) {
            var books = document.querySelectorAll('.card');
            books.forEach((book, i) => {
                if (i < 6) {
                    var btitle = book.querySelector('h5')?.textContent || '';
                    var bauthor = book.querySelector('.text-muted')?.textContent || '';
                    pageContent += `${i+1}. ${btitle} - ${bauthor}\n`;
                }
            });
            if (pageContent) pageContent = '当前页面展示的图书：\n' + pageContent;
        } else if (path.includes('mine.html')) {
            var borrows = document.querySelectorAll('table tr');
            borrows.forEach((row, i) => {
                if (i > 0 && i < 6) {
                    var cells = row.querySelectorAll('td');
                    var btitle = cells[1]?.textContent || '';
                    var status = cells[4]?.textContent || '';
                    pageContent += `${i}. ${btitle} - ${status}\n`;
                }
            });
            if (pageContent) pageContent = '我的借阅记录：\n' + pageContent;
        } else if (path.includes('learn.html')) {
            var question = document.querySelector('.question-text')?.textContent || '';
            var options = document.querySelectorAll('.option-item');
            pageContent = `题目：${question}\n选项：`;
            options.forEach((opt, i) => {
                pageContent += `\n${String.fromCharCode(65 + i)}. ${opt?.textContent || ''}`;
            });
        }

        return pageContent.trim();
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function createToggleButton() {
        if (document.getElementById('live2d-toggle')) return;
        
        var btn = document.createElement('button');
        btn.id = 'live2d-toggle';
        btn.innerHTML = isHidden ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        btn.style.cssText = 'position:fixed;right:10px;bottom:480px;width:36px;height:36px;border-radius:50%;background:rgba(54,59,63,0.9);border:1px solid #4a5056;color:#e0e0e0;cursor:pointer;z-index:9999;display:flex;align-items:center;justify-content:center;font-size:14px;transition:all .2s;opacity:0.7;';
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
        var chatPanel = document.getElementById('live2d-chat-panel');
        var btn = document.getElementById('live2d-toggle');
        
        if (widget) {
            widget.style.display = isHidden ? 'none' : 'block';
        }
        if (container) {
            container.style.display = isHidden ? 'none' : 'block';
        }
        if (chatPanel) {
            chatPanel.style.display = isHidden ? 'none' : 'flex';
        }
        if (btn) {
            btn.innerHTML = isHidden ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
        }
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
            
            createChatPanel();
            createToggleButton();
            
            if (isHidden) {
                var widget = document.getElementById('live2d-widget');
                var chatPanel = document.getElementById('live2d-chat-panel');
                if (widget) widget.style.display = 'none';
                if (chatPanel) chatPanel.style.display = 'none';
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

    setInterval(showTip, 30000);
})();