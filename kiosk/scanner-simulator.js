// 扫描枪模拟脚本 - 在浏览器控制台运行
// 模拟扫描枪快速输入ISBN并自动回车

function simulateScanner(isbn = '9787115545527') {
    const input = document.getElementById('isbnInput');
    if (!input) {
        console.error('未找到输入框，请确保在借书页面');
        return;
    }

    input.focus();
    console.log('开始模拟扫描枪输入:', isbn);

    // 模拟扫描枪逐字符快速输入
    let i = 0;
    const interval = setInterval(() => {
        if (i < isbn.length) {
            input.value += isbn[i];
            i++;
        } else {
            clearInterval(interval);
            console.log('输入完成，触发回车');
            // 模拟回车键
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
        }
    }, 50); // 每50ms输入一个字符，模拟真实扫描枪速度
}

// 使用方法：
// simulateScanner('9787115545527')  // 默认ISBN
// simulateScanner('9787556848768')  // 自定义ISBN
