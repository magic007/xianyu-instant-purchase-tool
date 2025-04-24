document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchResults = document.getElementById('searchResults');
    const searchResultsTable = document.getElementById('searchResultsTable');
    const resultStats = document.getElementById('resultStats');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const clearCollectionsBtn = document.getElementById('clearCollections');
    const itemTemplate = document.getElementById('itemTemplate');
    const tableRowTemplate = document.getElementById('tableRowTemplate');
    const gridViewBtn = document.getElementById('gridViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');
    const gridView = document.getElementById('gridView');
    const tableView = document.getElementById('tableView');
    const advancedSearchToggle = document.querySelector('[data-bs-toggle="collapse"]');
    const locationSelect = document.getElementById('location');
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    const refreshIntervalInput = document.getElementById('refreshInterval');
    
    // 自动刷新计时器
    let refreshTimer = null;
    
    // 更新自动刷新状态
    function updateAutoRefresh() {
        // 清除现有的定时器
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
        
        // 如果启用了自动刷新，设置新的定时器
        if (autoRefreshCheckbox.checked) {
            const interval = Math.max(5, parseInt(refreshIntervalInput.value) || 30) * 1000;
            refreshTimer = setInterval(function() {
                // 只有在非加载状态才触发搜索
                if (loadingIndicator.classList.contains('d-none')) {
                    // 如果已经有搜索结果，则进行刷新搜索
                    if (searchResults.children.length > 0 || searchResultsTable.children.length > 0) {
                        // 保存搜索滚动位置
                        const scrollPosition = window.scrollY;
                        
                        // 触发表单提交事件
                        const submitEvent = new Event('submit', {
                            'bubbles': true,
                            'cancelable': true
                        });
                        searchForm.dispatchEvent(submitEvent);
                        
                        // 添加刷新指示器
                        const refreshIndicator = document.createElement('div');
                        refreshIndicator.className = 'auto-refresh-indicator';
                        refreshIndicator.innerHTML = `<small class="text-muted">自动刷新于 ${new Date().toLocaleTimeString()}</small>`;
                        resultStats.appendChild(refreshIndicator);
                        
                        // 自动刷新后3秒移除指示器
                        setTimeout(() => {
                            if (refreshIndicator && refreshIndicator.parentNode) {
                                refreshIndicator.parentNode.removeChild(refreshIndicator);
                            }
                            
                            // 恢复滚动位置
                            window.scrollTo(0, scrollPosition);
                        }, 3000);
                    }
                }
            }, interval);
            
            console.log(`启用自动刷新，每 ${interval/1000} 秒刷新一次`);
        } else {
            console.log('禁用自动刷新');
        }
    }
    
    // 监听自动刷新选项变化
    autoRefreshCheckbox.addEventListener('change', updateAutoRefresh);
    refreshIntervalInput.addEventListener('change', function() {
        if (autoRefreshCheckbox.checked) {
            updateAutoRefresh();
        }
    });
    
    // 页面卸载时清除定时器
    window.addEventListener('beforeunload', function() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
        }
    });
    
    // 视图切换
    gridViewBtn.addEventListener('click', function() {
        gridView.style.display = 'block';
        tableView.style.display = 'none';
        gridViewBtn.classList.add('active');
        tableViewBtn.classList.remove('active');
    });
    
    tableViewBtn.addEventListener('click', function() {
        gridView.style.display = 'none';
        tableView.style.display = 'block';
        gridViewBtn.classList.remove('active');
        tableViewBtn.classList.add('active');
    });
    
    // 加载地区列表
    loadLocations();
    
    // 判断是否使用高级搜索
    let useAdvancedSearch = false;
    
    // 监听高级搜索折叠状态变化
    document.getElementById('advancedSearch').addEventListener('shown.bs.collapse', function() {
        useAdvancedSearch = true;
    });
    
    document.getElementById('advancedSearch').addEventListener('hidden.bs.collapse', function() {
        useAdvancedSearch = false;
    });
    
    // 搜索事件处理
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // 显示加载指示器
        searchResults.innerHTML = '';
        searchResultsTable.innerHTML = '';
        resultStats.textContent = '';
        loadingIndicator.classList.remove('d-none');
        errorMessage.classList.add('d-none');
        
        // 获取表单数据
        const formData = new FormData(searchForm);
        
        // 处理复选框
        if (document.getElementById('isAttention').checked) {
            formData.set('is_attention', 'true');
        } else {
            formData.set('is_attention', 'false');
        }
        
        // 使用高级搜索还是简单搜索
        const searchEndpoint = useAdvancedSearch ? '/advanced_search' : '/simple_search';
        
        // 发送搜索请求
        fetch(searchEndpoint, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 隐藏加载指示器
            loadingIndicator.classList.add('d-none');
            
            if (data.success) {
                resultStats.textContent = data.message;
                
                // 显示搜索结果
                if (data.items.length > 0) {
                    console.log("服务器返回的数据:", JSON.stringify(data.items[0]));
                    displaySearchResults(data.items);
                    
                    // 检查是否需要启动自动刷新
                    if (autoRefreshCheckbox.checked && !refreshTimer) {
                        updateAutoRefresh();
                    }
                } else {
                    const emptyMessage = '<div class="col-12 empty-results"><i class="bi bi-search" style="font-size: 2rem;"></i><p class="mt-3">没有找到匹配的商品</p></div>';
                    searchResults.innerHTML = emptyMessage;
                    searchResultsTable.innerHTML = `<tr><td colspan="6" class="text-center py-5">${emptyMessage}</td></tr>`;
                }
            } else {
                // 显示错误信息
                errorMessage.textContent = data.message;
                errorMessage.classList.remove('d-none');
            }
        })
        .catch(error => {
            // 处理错误
            loadingIndicator.classList.add('d-none');
            errorMessage.textContent = '搜索请求失败：' + error.message;
            errorMessage.classList.remove('d-none');
        });
    });
    
    // 显示搜索结果
    function displaySearchResults(items) {
        searchResults.innerHTML = '';
        searchResultsTable.innerHTML = '';
        
        items.forEach(item => {
            console.log("处理商品:", item.title);
            console.log("价格信息:", item.price);
            console.log("发布时间:", item.postTime);
            console.log("位置信息:", item.location);
            console.log("图片信息:", item.image);
            console.log("标签信息:", item.tags);
            console.log("用户昵称:", item.userName);
            
            // 卡片视图
            const itemNode = document.importNode(itemTemplate.content, true);
            
            // 填充数据
            itemNode.querySelector('.item-title').textContent = item.title;
            itemNode.querySelector('.item-price').textContent = item.price || "未知价格";
            
            // 填充额外信息（如果有）
            const locationElement = itemNode.querySelector('.item-location');
            if (item.location && item.location.trim() !== '') {
                locationElement.innerHTML = `<i class="bi bi-geo-alt"></i> ${item.location}`;
                locationElement.style.display = 'inline-block';
            } else {
                locationElement.style.display = 'none';
            }
            
            const postTimeElement = itemNode.querySelector('.item-post-time');
            if (item.postTime && item.postTime.trim() !== '') {
                postTimeElement.innerHTML = `<i class="bi bi-clock"></i> ${item.postTime}`;
                postTimeElement.style.display = 'inline-block';
            } else {
                postTimeElement.style.display = 'none';
            }
            
            // 检查.item-details元素是否存在，如果不存在则找一个合适的父元素
            const detailsContainer = itemNode.querySelector('.item-details') || 
                                    itemNode.querySelector('.card-body');
            
            // 添加用户昵称（如果有）
            if (item.userName && item.userName.trim() !== '') {
                const userElement = document.createElement('div');
                userElement.className = 'item-user text-muted mt-1';
                userElement.innerHTML = `<i class="bi bi-person"></i> ${item.userName}`;
                detailsContainer.appendChild(userElement);
            }
            
            // 添加标签（如果有）
            if (item.tags && item.tags.length > 0) {
                const tagsContainer = document.createElement('div');
                tagsContainer.className = 'item-tags mt-2';
                
                item.tags.forEach(tag => {
                    if (tag) {
                        const tagElement = document.createElement('span');
                        
                        // 根据标签内容设置不同的样式
                        if (tag === 'freeShippingIcon') {
                            // 对包邮图标特殊处理
                            tagElement.className = 'badge bg-danger text-white me-1 mb-1';
                            tagElement.textContent = '包邮';
                        } else if (tag.includes('上新')) {
                            // 对上新标签特殊处理，使用绿色背景
                            tagElement.className = 'badge bg-success text-white me-1 mb-1';
                            tagElement.textContent = tag;
                        } else if (tag.includes('发布') || tag.includes('小时前') || tag.includes('分钟前')) {
                            // 对发布时间标签特殊处理，使用浅黄色背景
                            tagElement.className = 'badge bg-warning text-dark me-1 mb-1';
                            tagElement.textContent = tag;
                        } else {
                            // 默认样式
                            tagElement.className = 'badge bg-light text-dark me-1 mb-1';
                            tagElement.textContent = tag;
                        }
                        
                        tagsContainer.appendChild(tagElement);
                    }
                });
                
                detailsContainer.appendChild(tagsContainer);
            }
            
            const imgElement = itemNode.querySelector('.item-image');
            if (item.image && item.image.trim() !== '') {
                console.log('设置商品图片URL:', item.image); // 调试信息
                imgElement.src = item.image;
                imgElement.onerror = function() {
                    console.log('图片加载失败，使用占位图');
                    this.src = 'https://via.placeholder.com/200x200?text=无法加载图片';
                };
            } else {
                console.log('商品无图片');
                imgElement.src = 'https://via.placeholder.com/200x200?text=无图片';
            }
            
            // 设置收藏按钮属性
            const addButton = itemNode.querySelector('.add-collection');
            addButton.dataset.itemId = item.itemId;
            
            // 设置聊天按钮属性
            const chatButton = itemNode.querySelector('.chat-btn');
            if (item.itemId) {
                // 构建聊天URL - 需要itemId和卖家userId (如果有)
                let chatUrl = `https://www.goofish.com/im?spm=a21ybx.item.want.1.46023da6vVfVzj&itemId=${item.itemId}`;
                
                // 如果有卖家userId，添加到URL
                if (item.sellerId) {
                    chatUrl += `&peerUserId=${item.sellerId}`;
                }
                
                chatButton.href = chatUrl;
                chatButton.title = "与卖家聊天";
            } else {
                chatButton.style.display = 'none'; // 如果没有商品ID，隐藏聊天按钮
            }
            
            // 设置立即下单按钮属性
            const buyNowButton = itemNode.querySelector('.buy-now-btn');
            if (item.itemId) {
                // 新逻辑：设置按钮点击事件，调用后端接口
                buyNowButton.removeAttribute('href'); // 移除链接属性
                buyNowButton.title = "点击开始秒杀任务";
                buyNowButton.dataset.itemId = item.itemId;
                buyNowButton.dataset.title = item.title;
                
                // 添加点击事件监听器
                buyNowButton.addEventListener('click', function() {
                    const btn = this;
                    const itemId = btn.dataset.itemId;
                    const title = btn.dataset.title;
                    triggerSeckill(itemId, title, btn);
                });
            } else {
                buyNowButton.style.display = 'none'; // 如果没有商品ID，隐藏下单按钮
            }
            
            // 添加到结果区域
            searchResults.appendChild(itemNode);
            
            // 表格视图
            const tableRow = document.importNode(tableRowTemplate.content, true);
            
            // 填充表格数据
            const titleElement = tableRow.querySelector('.item-title');
            titleElement.textContent = item.title;
            
            // 添加用户昵称和标签到表格视图的标题列
            if (item.userName || (item.tags && item.tags.length > 0)) {
                const extraInfo = document.createElement('div');
                extraInfo.className = 'small mt-1';
                
                if (item.userName) {
                    const userSpan = document.createElement('span');
                    userSpan.className = 'text-muted me-2';
                    userSpan.innerHTML = `<i class="bi bi-person"></i> ${item.userName}`;
                    extraInfo.appendChild(userSpan);
                }
                
                if (item.tags && item.tags.length > 0) {
                    item.tags.forEach(tag => {
                        if (tag) {
                            const tagSpan = document.createElement('span');
                            
                            // 根据标签内容设置不同的样式
                            if (tag === 'freeShippingIcon') {
                                // 对包邮图标特殊处理
                                tagSpan.className = 'badge bg-danger text-white me-1';
                                tagSpan.textContent = '包邮';
                            } else if (tag.includes('上新')) {
                                // 对上新标签特殊处理，使用绿色背景
                                tagSpan.className = 'badge bg-success text-white me-1';
                                tagSpan.textContent = tag;
                            } else if (tag.includes('发布') || tag.includes('小时前') || tag.includes('分钟前')) {
                                // 对发布时间标签特殊处理，使用浅黄色背景
                                tagSpan.className = 'badge bg-warning text-dark me-1';
                                tagSpan.textContent = tag;
                            } else {
                                // 默认样式
                                tagSpan.className = 'badge bg-light text-dark me-1';
                                tagSpan.textContent = tag;
                            }
                            
                            extraInfo.appendChild(tagSpan);
                        }
                    });
                }
                
                titleElement.appendChild(document.createElement('br'));
                titleElement.appendChild(extraInfo);
            }
            
            tableRow.querySelector('.item-price').textContent = item.price || "未知价格";
            tableRow.querySelector('.item-post-time').textContent = item.postTime || '未知';
            tableRow.querySelector('.item-location').textContent = item.location || '未知';
            
            const tableImgElement = tableRow.querySelector('.item-image');
            if (item.image && item.image.trim() !== '') {
                tableImgElement.src = item.image;
                tableImgElement.onerror = function() {
                    this.src = 'https://via.placeholder.com/90x90?text=无法加载';
                };
            } else {
                tableImgElement.src = 'https://via.placeholder.com/90x90?text=无图片';
            }
            
            // 设置收藏按钮属性
            const tableAddButton = tableRow.querySelector('.add-collection');
            tableAddButton.dataset.itemId = item.itemId;
            
            // 设置表格视图中的聊天按钮属性
            const tableChatButton = tableRow.querySelector('.chat-btn');
            if (item.itemId) {
                // 构建聊天URL - 需要itemId和卖家userId (如果有)
                let chatUrl = `https://www.goofish.com/im?spm=a21ybx.item.want.1.46023da6vVfVzj&itemId=${item.itemId}`;
                
                // 如果有卖家userId，添加到URL
                if (item.sellerId) {
                    chatUrl += `&peerUserId=${item.sellerId}`;
                }
                
                tableChatButton.href = chatUrl;
                tableChatButton.title = "与卖家聊天";
            } else {
                tableChatButton.style.display = 'none'; // 如果没有商品ID，隐藏聊天按钮
            }
            
            // 设置表格视图中的立即下单按钮属性
            const tableBuyNowButton = tableRow.querySelector('.buy-now-btn');
            if (item.itemId) {
                // 新逻辑：设置按钮点击事件，调用后端接口
                tableBuyNowButton.removeAttribute('href'); // 移除链接属性
                tableBuyNowButton.title = "点击开始秒杀任务";
                tableBuyNowButton.dataset.itemId = item.itemId;
                tableBuyNowButton.dataset.title = item.title;
                
                // 添加点击事件监听器
                tableBuyNowButton.addEventListener('click', function() {
                    const btn = this;
                    const itemId = btn.dataset.itemId;
                    const title = btn.dataset.title;
                    triggerSeckill(itemId, title, btn);
                });
            } else {
                tableBuyNowButton.style.display = 'none'; // 如果没有商品ID，隐藏下单按钮
            }
            
            // 添加到表格结果区域
            searchResultsTable.appendChild(tableRow);
        });
        
        // 为所有收藏按钮添加事件监听
        document.querySelectorAll('.add-collection').forEach(button => {
            button.addEventListener('click', function() {
                const itemId = this.dataset.itemId;
                addToCollection(itemId, this);
            });
        });
    }
    
    // 加载地区列表
    function loadLocations() {
        fetch('/get_locations')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.locations) {
                    data.locations.forEach(location => {
                        const option = document.createElement('option');
                        option.value = location.code;
                        option.textContent = location.name;
                        locationSelect.appendChild(option);
                    });
                }
            })
            .catch(error => {
                console.error('加载地区列表失败:', error);
            });
    }
    
    // 添加到收藏
    function addToCollection(itemId, buttonElement) {
        // 禁用按钮，防止重复点击
        buttonElement.disabled = true;
        buttonElement.textContent = '添加中...';
        
        const formData = new FormData();
        formData.append('item_id', itemId);
        
        fetch('/add_collection', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                buttonElement.textContent = '已收藏';
                buttonElement.classList.remove('btn-primary');
                buttonElement.classList.add('btn-success');
            } else {
                buttonElement.textContent = '添加失败';
                buttonElement.classList.remove('btn-primary');
                buttonElement.classList.add('btn-danger');
                buttonElement.disabled = false;
                
                // 显示错误消息
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            buttonElement.textContent = '添加失败';
            buttonElement.classList.remove('btn-primary');
            buttonElement.classList.add('btn-danger');
            buttonElement.disabled = false;
            
            // 显示错误消息
            showToast('添加收藏失败：' + error.message, 'danger');
        });
    }
    
    // 清空收藏列表
    clearCollectionsBtn.addEventListener('click', function() {
        if (!confirm('确定要清空收藏列表吗？此操作不可恢复。')) {
            return;
        }
        
        this.disabled = true;
        this.innerHTML = '<i class="bi bi-hourglass-split"></i> 正在清空...';
        
        fetch('/clear_collections', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-trash"></i> 清空收藏列表';
            
            if (data.success) {
                showToast(data.message, 'success');
            } else {
                showToast(data.message, 'danger');
            }
        })
        .catch(error => {
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-trash"></i> 清空收藏列表';
            showToast('清空收藏列表失败：' + error.message, 'danger');
        });
    });
    
    // 显示通知
    function showToast(message, type) {
        // 检查是否已存在toast容器
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        // 创建新的toast
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = `toast show bg-${type} text-white`;
        toast.id = toastId;
        toast.role = 'alert';
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${type === 'success' ? '成功' : '错误'}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // 添加到容器
        toastContainer.appendChild(toast);
        
        // 3秒后自动关闭
        setTimeout(() => {
            toast.remove();
        }, 3000);
        
        // 为关闭按钮添加事件
        toast.querySelector('.btn-close').addEventListener('click', function() {
            toast.remove();
        });
    }
    
    // 新增：秒杀下单函数
    function triggerSeckill(itemId, title, buttonElement) {
        if (!itemId) {
            showToast('商品ID无效，无法跳转到下单页面', 'danger');
            return;
        }
        
        // 构建下单页面URL
        const orderUrl = `https://www.goofish.com/create-order?itemId=${itemId}`;
        
        // 禁用按钮，防止重复点击
        buttonElement.disabled = true;
        buttonElement.textContent = '跳转中...';
        
        // 设置短暂延迟后跳转，给用户视觉反馈
        setTimeout(() => {
            window.open(orderUrl, '_blank');
            // 恢复按钮状态
            buttonElement.disabled = false;
            buttonElement.textContent = '立即下单';
        }, 300);
    }
}); 