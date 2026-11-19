/* FrontierLab frontend — vanilla JavaScript, no external dependency. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const state = { items: [], view: 'all', topic: '全部方向', days: '30', sort: 'newest', search: '', saved: new Set(), meta: {} };
  try { state.saved = new Set(JSON.parse(localStorage.getItem('frontierlab:saved') || '[]')); } catch (_) { state.saved = new Set(); }
  const escape = (x) => String(x ?? '').replace(/[&<>"']/g, (ch) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[ch]));
  const url = (x) => { try { const v = new URL(x); return /^https?:$/.test(v.protocol) ? v.href : ''; } catch (_) { return ''; } };
  const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()).replaceAll('/', '-');
  const age = (iso) => { const a = Date.parse(iso + 'T00:00:00Z'), b = Date.parse(today() + 'T00:00:00Z'); return Number.isFinite(a) ? Math.floor((b - a) / 86400000) : Infinity; };
  const pretty = (iso) => /^\d{4}-\d{2}-\d{2}$/.test(iso || '') ? iso.slice(0, 4) + '.' + iso.slice(5, 7) + '.' + iso.slice(8) : (iso || '未知日期');
  const typeName = (a) => a.type === 'insight' ? '权威资讯' : '研究论文';
  const isCurated = (a) => Boolean(a.editorial);
  function saveState() { try { localStorage.setItem('frontierlab:saved', JSON.stringify([...state.saved])); } catch (_) { /* storage disabled */ } }
  let toastTimer;
  function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), 2600); }
  function matchesTopic(a) {
    if (state.topic === '全部方向') return true;
    const text = [a.category, ...(a.topics || []), a.title_zh || '', a.problem || '', a.title || ''].join(' ').toLowerCase();
    const dict = { '动态图': ['动态图','动态依赖','动态空间','graph'], '自监督学习': ['自监督','self-supervised','mask reconstruction','contrastive'], '事件': ['事件','事故','异常扰动','非周期','incident','aperiodic'], '多模态': ['多模态','外部因素','天气','weather','condition','llm'], '泛化': ['泛化','跨域','零样本','zero-shot','transfer'] };
    return (dict[state.topic] || [state.topic]).some(t => text.includes(t.toLowerCase()));
  }
  function filtered() {
    let list = state.items.filter(a => {
      if (state.view === 'paper' && a.type !== 'paper') return false;
      if (state.view === 'insight' && a.type !== 'insight') return false;
      if (state.view === 'saved' && !state.saved.has(a.id)) return false;
      if (state.view !== 'saved' && state.days !== 'all' && !(age(a.date) >= 0 && age(a.date) <= Number(state.days))) return false;
      if (!matchesTopic(a)) return false;
      if (state.search) {
        const t = [a.title, a.title_zh, a.source, a.venue, a.category, ...(a.topics || []), a.problem, a.method, a.relevance].join(' ').toLowerCase();
        if (!t.includes(state.search.toLowerCase())) return false;
      }
      return true;
    });
    list.sort((a,b) => state.sort === 'curated' ? (Number(isCurated(b)) - Number(isCurated(a)) || (b.date || '').localeCompare(a.date || '')) : (b.date || '').localeCompare(a.date || '') || Number(isCurated(b)) - Number(isCurated(a)));
    return list;
  }
  function rankLabel(a) { return a.level || '评级待核实'; }
  function card(a) {
    const published = age(a.date);
    const fresh = published >= 0 && published <= 7;
    const isSaved = state.saved.has(a.id);
    return `<article class="paper-card"><div class="paper-header"><div class="tags"><span class="tag ${a.type === 'insight' ? 'tag-orange' : ''}">${typeName(a)}</span><span class="tag tag-secondary">${escape(a.category || '时空预测')}</span>${isCurated(a) ? '<span class="tag tag-gray">人工精选</span>' : '<span class="tag tag-gray">自动发现 · 待核验</span>'}${fresh ? '<span class="tag">近7天</span>' : ''}</div><time class="paper-date" datetime="${escape(a.date)}">${pretty(a.date)}</time></div>
      <h3 class="paper-title">${escape(a.title_zh || a.title)}</h3><div class="paper-en">${escape(a.title)}</div>
      <p class="paper-summary"><b>研究问题：</b>${escape(a.problem || '待阅读原文后核验')}</p>
      <div class="paper-relevance"><b>与你的研究关联：</b> ${escape(a.relevance || '此条由数据库自动发现，关联性尚未人工评估。')}</div>
      <div class="paper-footer"><div class="venue"><span class="venue-mark">${a.type === 'insight' ? 'N' : 'P'}</span><span title="${escape(a.status || '')}">${escape(a.venue || a.source || '来源待核实')} · ${escape(a.status || '未核实')}</span></div><div class="card-actions"><a class="link-action" href="${escape(url(a.url) || '#')}" target="_blank" rel="noopener noreferrer">原文 ↗</a><button class="save-action ${isSaved ? 'saved' : ''}" data-save="${escape(a.id)}" aria-label="${isSaved ? '取消收藏' : '收藏'}" title="${isSaved ? '取消收藏' : '收藏'}">${isSaved ? '★' : '☆'}</button><button class="detail-action" data-detail="${escape(a.id)}">查看解读 →</button></div></div></article>`;
  }
  function render() {
    const list = filtered();
    $('allCount').textContent = String(state.items.length);
    $('paperStat').textContent = String(state.items.filter(x => x.type === 'paper').length).padStart(2,'0');
    $('insightStat').textContent = String(state.items.filter(x => x.type === 'insight').length).padStart(2,'0');
    $('editorStat').textContent = String(state.items.filter(isCurated).length).padStart(2,'0');
    $('weekStat').textContent = String(state.items.filter(x => age(x.date) >= 0 && age(x.date) <= 7).length).padStart(2,'0');
    $('feedCount').textContent = `${list.length} 条`;
    $('feedHeading').firstChild.textContent = ({all:'前沿动态 ',paper:'研究论文 ',insight:'权威资讯 ',saved:'我的收藏 '})[state.view];
    $('feedHint').textContent = state.view === 'saved' ? '你的本地浏览器收藏。可以导出备份。' : `按原始发布日期排序 · ${state.days === 'all' ? '历史全部' : '近' + state.days + '天'} · 评级不会自动推断`;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.view === state.view));
    document.querySelectorAll('.tab').forEach(el => el.classList.toggle('active', el.dataset.tab === state.view));
    document.querySelectorAll('.topic-item').forEach(el => el.classList.toggle('selected', el.dataset.topic === state.topic));
    $('cardList').innerHTML = list.length ? list.map(card).join('') : `<div class="empty-state"><div class="empty-symbol">⌁</div><strong>当前条件下没有匹配内容</strong><small>可调整时间范围、研究方向或关键词。没有新论文并不代表自动补造更新；宁缺毋滥。</small></div>`;
    $('listFooter').textContent = `显示 ${list.length} 条 · ${state.items.length} 条总收录 · 仅“人工精选”包含人工研究解读；其他为自动发现候选`;
    renderSignals();
  }
  function renderSignals() {
    const keys = [ ['动态图','动态图'], ['交通预测','交通预测'], ['事件','事件/异常'], ['多模态','多模态'], ['泛化','跨域泛化'] ];
    const counts = keys.map(([k,label]) => ({ key:k, label, count:state.items.filter(a => ([a.category,...(a.topics || []), a.title_zh, a.problem].join(' ')).includes(k) || (k === '事件' && /非周期|事故|事件/.test([a.category,...(a.topics || [])].join(' ')))).length }));
    const max = Math.max(1,...counts.map(x=>x.count));
    const colors = ['#5a88e8','#4d9ce8','#2bbba7','#a590df','#e8a16a'];
    $('signalBars').innerHTML = counts.map((x,i) => `<div><div class="signal-label"><span>${escape(x.label)}</span><b>${x.count}</b></div><div class="signal-track"><div class="signal-fill" style="--bar:${colors[i]};width:${Math.round(100*x.count/max)}%"></div></div></div>`).join('');
  }
  function detail(id) {
    const a = state.items.find(x => x.id === id); if (!a) return;
    const topics = [typeName(a),a.category,a.status].filter(Boolean).map(t => `<span class="tag tag-secondary">${escape(t)}</span>`).join('');
    $('modalContent').innerHTML = `<h2 class="modal-title" id="detailTitle">${escape(a.title_zh || a.title)}</h2><div class="modal-en">${escape(a.title)}</div><div class="modal-meta">${topics}<span class="tag tag-gray">${pretty(a.date)}</span></div>
      <section class="modal-section"><h4>01 · 研究问题 / Existing gap</h4><p>${escape(a.problem || '研究问题待全文阅读与核验。')}</p></section>
      <section class="modal-section"><h4>02 · 核心方法 / Method</h4><p>${escape(a.method || '自动候选：仅记录原始元数据，请查看原文核验核心方法。')}</p></section>
      <section class="modal-section"><h4>03 · 贡献与证据 / Contribution</h4><p>${escape(a.contribution || '待人工审阅，数据库自动收录不代表已验证创新性。')}</p></section>
      <section class="modal-section"><h4>04 · 对当前研究的启发</h4><p>${escape(a.relevance || '关联性待研究者进一步审阅。')}</p></section>
      ${a.questions?.length ? `<section class="modal-section"><h4>05 · 建议检查的问题</h4><ul>${a.questions.map(q=>`<li>${escape(q)}</li>`).join('')}</ul></section>` : ''}
      <section class="modal-section"><h4>来源与评级核验</h4><p>来源：${escape(a.source)}<br>状态：${escape(a.status)}<br>刊会与等级：${escape(rankLabel(a))}${a.doi ? `<br>DOI：${escape(a.doi)}` : ''}<br>分析类型：${a.editorial ? '人工整理，须以原文为准' : '程序发现，内容待人工核验'}</p></section>
      <div class="modal-links"><a class="modal-link" href="${escape(url(a.url)||'#')}" target="_blank" rel="noopener noreferrer">阅读原文 ↗</a>${a.code && url(a.code)?`<a class="modal-link alt" href="${escape(url(a.code))}" target="_blank" rel="noopener noreferrer">查看代码 ↗</a>`:''}<button class="modal-link alt" id="copyCitation">复制引用信息</button></div>`;
    $('modalBackdrop').hidden = false; document.body.style.overflow = 'hidden';
    $('copyCitation').addEventListener('click', () => { const s = `${a.title}. ${a.venue||a.source}, ${a.date}. ${a.doi?'DOI: '+a.doi+' · ':''}${a.url}`; navigator.clipboard?.writeText(s).then(()=>toast('引用信息已复制')).catch(()=>toast('当前环境不支持复制')); });
  }
  function closeModal(){ $('modalBackdrop').hidden = true; document.body.style.overflow = ''; }
  function method(){
    $('modalContent').innerHTML = `<h2 class="modal-title" id="detailTitle">关于内容筛选、学术评级与可靠性</h2><div class="modal-en">Evidence before impressions · 以事实为先</div><section class="modal-section"><h4>论文发现</h4><p>使用 OpenAlex、arXiv 论文元数据检索。程序按题目与摘要过滤交通流预测相关主题，并对 DOI / 链接去重。自动抓取属于候选清单，不意味着阅读全文、评审结论或领域排名。</p></section><section class="modal-section"><h4>人工精选</h4><p>人工记录研究问题、技术方法、与已有研究的关系及可能验证点。每条保留直接原文链接；未能独立核实的事实不会转化成确定性结论。</p></section><section class="modal-section"><h4>中科院分区 / JCR / CCF</h4><p>三个体系不同，分区还区分版本与年份。程序不根据期刊名直接推断等级；如未查询到对应年份的官方分区或会议名录，显示“待核实”。arXiv 是预印本平台，不能用其分类代替会议录用证明。</p></section><section class="modal-section"><h4>微信公众号</h4><p>公众号通常没有稳定开放的官方检索接口，默认仅人工收录有完整、公开、可核验链接的文章，不爬取受保护内容，也不伪造来源。</p></section><section class="modal-section"><h4>时间范围与数据可靠性</h4><p>“近7天”是根据来源发布日期计算，并非网页上一次刷新时间。GitHub Actions 计划每周五 09:00（北京时间）运行；实际执行时间可能有延迟，失败时保留已有数据，不会伪装已更新。</p></section>`;
    $('modalBackdrop').hidden=false; document.body.style.overflow='hidden';
  }
  function exportSaved(){
    const items = state.items.filter(a => state.saved.has(a.id));
    if (!items.length) { toast('还没有收藏的论文或资讯'); return; }
    const blob = new Blob([JSON.stringify({exported_at:new Date().toISOString(),items},null,2)],{type:'application/json'});
    const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='frontierlab-saved-'+today()+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);toast('收藏已导出');
  }
  function bind(){
    document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>{state.view=el.dataset.view;render();$('sidebar').classList.remove('open');}));
    document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',()=>{state.view=el.dataset.tab;render();}));
    document.querySelectorAll('[data-topic]').forEach(el=>el.addEventListener('click',()=>{state.topic=el.dataset.topic;render();$('sidebar').classList.remove('open');}));
    $('searchInput').addEventListener('input',(e)=>{state.search=e.target.value.trim();render();});
    $('timeFilter').addEventListener('change',(e)=>{state.days=e.target.value;render();});
    $('sortFilter').addEventListener('change',(e)=>{state.sort=e.target.value;render();});
    $('cardList').addEventListener('click',(e)=>{const save=e.target.closest('[data-save]'),details=e.target.closest('[data-detail]');if(save){const id=save.dataset.save;if(state.saved.has(id)){state.saved.delete(id);toast('已取消收藏');}else{state.saved.add(id);toast('已收藏到本地浏览器');}saveState();render();}if(details){detail(details.dataset.detail);}});
    $('mobileMenu').addEventListener('click',()=>$('sidebar').classList.toggle('open'));
    $('heroExplore').addEventListener('click',()=>{$('feedSection').scrollIntoView({behavior:'smooth'});state.sort='curated';$('sortFilter').value='curated';render();});
    ['heroMethod','footerMethod'].forEach(x=>$(x).addEventListener('click',method));
    $('exportSaved').addEventListener('click',exportSaved);
    $('closeModal').addEventListener('click',closeModal);
    $('modalBackdrop').addEventListener('click',(e)=>{if(e.target === $('modalBackdrop'))closeModal();});
    document.addEventListener('keydown',(e)=>{if(e.key==='Escape')closeModal();if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName) && $('modalBackdrop').hidden){e.preventDefault();$('searchInput').focus();}});
  }
  async function load(){
    const now = new Date();const shanghai = new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'long',day:'numeric',weekday:'long'}).format(now);
    $('todayLabel').textContent = shanghai;
    const iso = today();const d = new Date(iso+'T00:00:00Z');const week = Math.ceil(((d-new Date(Date.UTC(d.getUTCFullYear(),0,1)))/86400000+1)/7);
    $('heroWeek').textContent = `${d.getUTCFullYear()} / 第 ${week} 周`;
    try {
      let data;try { const r=await fetch('data.json',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status); data=await r.json(); } catch(err) { if(!window.FRONTIER_INITIAL_DATA)throw err;data=window.FRONTIER_INITIAL_DATA; }
      if(!Array.isArray(data.items))throw Error('数据格式无效');
      state.items=data.items.filter(a=>a&&a.id&&a.title&&url(a.url));state.meta=data;
      const stamp=data.generated_at?new Date(data.generated_at):null;
      $('updatedLabel').textContent=stamp&&!isNaN(stamp)?`数据生成于 ${new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(stamp)} · 北京时间`:'数据时间待核对';
      if(data.fetch_status && data.fetch_status.every(x=>!x.ok)){$('updatedLabel').title='最新自动采集未成功，展示已存储的历史内容';}
      render();
    }catch(err){$('updatedLabel').textContent='数据暂不可用';$('cardList').innerHTML=`<div class="empty-state"><strong>未能读取内容数据</strong><small>请检查 site/data.json 是否存在；本地预览可使用 python -m http.server。</small></div>`;}
  }
  bind();load();
})();
