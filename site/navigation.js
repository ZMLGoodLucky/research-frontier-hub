/* FrontierLab v1.5 — true dashboard and section navigation.
   Static pages share one document but only the selected workspace is visible.
   Hash links work on GitHub Pages and remain bookmarkable. */
(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const PAGES={
    home:{label:'首页概览',title:'今日科研概览',intro:'重点内容一目了然；进入专题栏目查看完整研究信息。',eyebrow:'RESEARCH DASHBOARD'},
    daily:{label:'每日精选',title:'每日研究精选',intro:'每天优选3–5篇论文；显示来源、日期和核验状态。',eyebrow:'DAILY PAPER DIGEST'},
    papers:{label:'论文雷达',title:'论文发现与检索',intro:'按研究主题、发表类型、时间与CCF等级检索。',eyebrow:'LITERATURE RADAR'},
    ideas:{label:'顶刊小论文选题',title:'单篇论文创新选题',intro:'一个深层科学问题、2–3项机制创新、可证伪实验与前人研究。',eyebrow:'RESEARCH PROBLEM STUDIO'},
    insights:{label:'权威资讯',title:'权威研究资讯',intro:'学术出版与研究机构动态，保留可信来源。',eyebrow:'TRUSTED RESEARCH SOURCES'},
    saved:{label:'我的收藏',title:'我的研究收藏',intro:'当前浏览器中的收藏条目，可随时导出。',eyebrow:'PERSONAL RESEARCH LIST'}
  };
  const feedMap={papers:'paper',insights:'insight',saved:'saved'};
  let active='';
  const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const url=x=>{try{const v=new URL(x);return /^https?:$/.test(v.protocol)?v.href:'';}catch{return ''}};
  const validPage=p=>Object.hasOwn(PAGES,p)?p:'home';
  function setPage(name,updateHash=true){
    const page=validPage(name);
    active=page;
    const sections={home:'homePage',daily:'dailyBrief',ideas:'innovationLab',research:'researchBody'};
    for(const [group,id] of Object.entries(sections)){
      const el=$(id);
      if(!el)continue;
      el.hidden= group==='research'? !['papers','insights','saved'].includes(page) : group!==page;
    }
    const metadata=PAGES[page];
    $('pageBreadcrumb').textContent=metadata.label;
    $('pageEyebrow').textContent=metadata.eyebrow;
    $('pageHeadline').textContent=metadata.title;
    $('pageDescription').textContent=metadata.intro;
    document.title=metadata.label+' · FrontierLab';
    document.querySelectorAll('[data-page]').forEach(el=>{
      const selected=el.dataset.page===page;
      el.classList.toggle('active',selected);
      el.setAttribute('aria-current',selected?'page':'false');
    });
    $('sidebar')?.classList.remove('open');
    document.body.dataset.activePage=page;
    if(updateHash && location.hash!==('#'+page))history.pushState(null,'','#'+page);
    if(page==='home')refreshDashboard();
    if(page==='papers'||page==='insights'||page==='saved'){
      // Existing paper app owns filters, collections and details. Its nav
      // handlers activate the corresponding feed before this handler runs.
      if(page==='papers' && typeof window.FrontierSetResearchView==='function')window.FrontierSetResearchView('paper');
      if(page==='insights' && typeof window.FrontierSetResearchView==='function')window.FrontierSetResearchView('insight');
      if(page==='saved' && typeof window.FrontierSetResearchView==='function')window.FrontierSetResearchView('saved');
    }
    window.scrollTo({top:0,behavior:'instant'});
    return page;
  }
  function renderPapers(data){
    const all=(data.items||[]).filter(x=>x.type==='paper');
    const ids=data.daily_digest?.ids||[];
    let selected=ids.map(id=>all.find(x=>x.id===id)).filter(Boolean).slice(0,3);
    if(!selected.length)selected=[...all].sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).slice(0,3);
    const date=data.daily_digest?.date||'';
    const isToday=date===new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    $('homePaperHeading').textContent=isToday?'今日重点论文':'最近一期重点论文';
    $('homePapers').innerHTML=selected.length?selected.map((a,i)=>`<div class="home-paper-item">
      <span class="home-paper-number">${String(i+1).padStart(2,'0')}</span>
      <div class="home-paper-copy"><a href="${escape(url(a.url)||'#')}" target="_blank" rel="noopener noreferrer">${escape(a.title_zh||a.title)}</a>
      <p>${escape(a.venue_abbr||a.venue||a.source||'刊会待核验')} · ${escape(a.date||'日期待核验')} · ${escape(a.cas_zone||'分区待核验')}</p></div>
      </div>`).join(''):'<div class="home-placeholder">目前暂无符合条件的论文，论文雷达仍可查看历史文献。</div>';
  }
  function renderMonitor(data){
    const status=data.fetch_status||[];
    const successes=status.filter(x=>x.ok).length,failures=status.filter(x=>!x.ok).length;
    let stamp='时间待核验';
    const date=new Date(data.last_checked_at||data.generated_at||'');
    if(!isNaN(date))stamp=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(date);
    $('homeMonitorBadge').textContent=failures?('有 '+failures+' 项异常'):(successes?'最近采集成功':'采集状态未知');
    $('homeMonitorBadge').classList.toggle('has-warnings',failures>0);
    $('homeSourceSummary').innerHTML=`<div class="home-status-main">
      <div><strong>${successes}</strong><span>成功来源</span></div>
      <div><strong>${failures}</strong><span>失败来源</span></div>
    </div><div class="home-last-sync">最近一次记录：${escape(stamp)} · 数据可能存在采集延迟</div>`;
  }
  async function refreshDashboard(){
    try {
      const r=await fetch('data.json',{cache:'no-store'});
      if(!r.ok)throw new Error('HTTP '+r.status);
      const data=await r.json();
      if(active!=='home')return;
      renderPapers(data);renderMonitor(data);
    } catch(e){
      const fallback=window.FRONTIER_INITIAL_DATA;
      if(fallback){renderPapers(fallback);renderMonitor(fallback);}
      else{
        $('homePapers').textContent='论文数据暂不可用。';
        $('homeSourceSummary').textContent='采集状态暂不可用。';
      }
    }
    try {
      const r=await fetch('research-ideas.json',{cache:'no-store'});
      if(!r.ok)throw Error('ideas unavailable');
      const ideas=await r.json();
      if(active!=='home')return;
      const top=(ideas.ideas||[])[0];
      $('homeIdea').innerHTML=top?`<span class="home-idea-badge">${escape(top.priority||'优先核查')}</span>
        <h3>${escape(top.title)}</h3>
        <p>${escape(top.core_claim||top.question)}</p>
        <div class="home-idea-scope">1篇独立小论文 · 3项候选创新 · 文献重叠待审</div>`:
        '<div class="home-placeholder">选题库暂无内容。</div>';
    }catch(e){$('homeIdea').textContent='选题库暂不可用，仍可从侧栏进入。';}
  }
  document.querySelectorAll('[data-page]').forEach(el=>el.addEventListener('click',()=>setPage(el.dataset.page)));
  document.querySelectorAll('[data-go-page]').forEach(el=>el.addEventListener('click',()=>setPage(el.dataset.goPage)));
  document.querySelectorAll('[data-topic]').forEach(el=>el.addEventListener('click',()=>setPage('papers')));
  document.querySelectorAll('[data-tab]').forEach(el=>el.addEventListener('click',e=>{
    const tab=el.dataset.tab;
    setPage(tab==='insight'?'insights':tab==='saved'?'saved':'papers');
  }));
  window.addEventListener('popstate',()=>setPage(location.hash.slice(1),false));
  window.addEventListener('hashchange',()=>setPage(location.hash.slice(1),false));
  window.FrontierNavigate={go:setPage};
  setPage(location.hash.slice(1),false);
})();
