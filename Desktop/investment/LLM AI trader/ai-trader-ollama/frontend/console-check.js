// 在瀏覽器控制台運行此腳本來檢查對話框是否被阻擋
// 複製整個文件內容，貼到瀏覽器控制台運行

console.log('=== 對話框診斷檢查 ===');

// 1. 檢查DOM元素
console.log('\n1. DOM元素檢查:');
const mainContent = document.getElementById('mainContent');
const convSection = document.getElementById('conversationsOverviewSection');
const convContainer = document.getElementById('conversationsOverview');

console.log('mainContent:', mainContent ? '✅ 存在' : '❌ 不存在');
console.log('conversationsOverviewSection:', convSection ? '✅ 存在' : '❌ 不存在');
console.log('conversationsOverview:', convContainer ? '✅ 存在' : '❌ 不存在');

// 2. 檢查CSS樣式
console.log('\n2. CSS樣式檢查:');
if (convSection) {
    const style = window.getComputedStyle(convSection);
    console.log('display:', style.display, style.display === 'none' ? '❌ 被隱藏' : '✅ 可見');
    console.log('visibility:', style.visibility, style.visibility === 'hidden' ? '❌ 被隱藏' : '✅ 可見');
    console.log('opacity:', style.opacity, parseFloat(style.opacity) === 0 ? '❌ 透明' : '✅ 不透明');
    console.log('z-index:', style.zIndex);
    console.log('width:', style.width);
    console.log('height:', style.height);
    console.log('position:', style.position);
}

// 3. 檢查父元素
console.log('\n3. 父元素檢查:');
if (convSection && convSection.parentElement) {
    const parent = convSection.parentElement;
    const parentStyle = window.getComputedStyle(parent);
    console.log('父元素:', parent.tagName, parent.id || parent.className);
    console.log('父元素 display:', parentStyle.display);
    console.log('父元素 visibility:', parentStyle.visibility);
    console.log('父元素 overflow:', parentStyle.overflow);
}

// 4. 檢查內容
console.log('\n4. 內容檢查:');
if (convContainer) {
    console.log('容器內容長度:', convContainer.innerHTML.length);
    console.log('容器內容預覽:', convContainer.innerHTML.substring(0, 200));
    console.log('是否有空狀態:', convContainer.innerHTML.includes('No conversations'));
    console.log('是否有對話列表:', convContainer.innerHTML.includes('conversation-list'));
}

// 5. 檢查JavaScript函數
console.log('\n5. JavaScript函數檢查:');
console.log('renderConversationsOverview:', typeof renderConversationsOverview === 'function' ? '✅ 存在' : '❌ 不存在');
console.log('fetchConversations:', typeof fetchConversations === 'function' ? '✅ 存在' : '❌ 不存在');
console.log('refreshData:', typeof refreshData === 'function' ? '✅ 存在' : '❌ 不存在');

// 6. 檢查API數據
console.log('\n6. API數據檢查:');
fetch('http://127.0.0.1:8000/api/agents/conversations?limit=10')
    .then(r => r.json())
    .then(data => {
        console.log('API響應:', data);
        console.log('對話數量:', data.conversations?.length || 0);
        if (data.conversations && data.conversations.length > 0) {
            console.log('✅ API返回了對話數據');
            console.log('最新對話:', data.conversations[0]);
        } else {
            console.log('⚠️ API沒有返回對話數據');
        }
    })
    .catch(e => {
        console.error('❌ API請求失敗:', e);
    });

// 7. 強制顯示對話區塊
console.log('\n7. 嘗試強制顯示:');
if (convSection) {
    convSection.style.display = 'block';
    convSection.style.visibility = 'visible';
    convSection.style.opacity = '1';
    convSection.style.zIndex = '1';
    console.log('✅ 已強制設置對話區塊為可見');
    
    const newStyle = window.getComputedStyle(convSection);
    console.log('更新後的樣式:');
    console.log('  display:', newStyle.display);
    console.log('  visibility:', newStyle.visibility);
    console.log('  opacity:', newStyle.opacity);
} else {
    console.log('❌ 無法強制顯示，因為元素不存在');
}

// 8. 手動觸發渲染
console.log('\n8. 手動觸發渲染:');
if (typeof fetchConversations === 'function' && typeof renderConversationsOverview === 'function') {
    console.log('正在手動獲取並渲染對話...');
    fetchConversations(30)
        .then(data => {
            console.log('獲取到的對話數據:', data);
            renderConversationsOverview(data.conversations || []);
            console.log('✅ 手動渲染完成');
        })
        .catch(e => {
            console.error('❌ 手動渲染失敗:', e);
        });
} else {
    console.log('❌ 無法手動觸發，因為函數不存在');
}

console.log('\n=== 診斷完成 ===');
console.log('如果對話框仍然不可見，請檢查:');
console.log('1. 是否有其他CSS覆蓋了樣式');
console.log('2. 是否有JavaScript錯誤阻止執行');
console.log('3. 是否有z-index問題導致被其他元素遮擋');
console.log('4. 是否有overflow:hidden導致內容被裁剪');

