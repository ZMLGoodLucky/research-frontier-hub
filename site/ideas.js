/* FrontierLab: weekly evidence-guided research-problem studio.
 * Human-reviewed hypotheses remain stable. Weekly machine-matched papers are
 * clearly marked as candidates, NOT as proof of novelty or prior art absence.
 */
(() => {
  'use strict';
  const container = document.getElementById('innovationIdeas');
  const state = document.getElementById('innovationStatus');
  const nav = document.getElementById('innovationNav');
  if (!container || !state) return;

  const esc = value => String(value == null ? '' : value).replace(/[&<>"']/g, c => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[c]));
  const safeLink = value => {
    try { const u = new URL(value); return ['http:', 'https:'].includes(u.protocol) ? u.href : ''; }
    catch (_) { return ''; }
  };
  const hyperlink = (raw, title) => {
    const href = safeLink(raw);
    return href ? `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(title)} ↗</a>` : esc(title);
  };
  const text = value => esc(value || '仍需核验');
  const refs = list => (list || []).map((p, i) => `<div class="idea-reference">
    <div class="idea-reference-title"><span class="idea-reference-number">${String(i + 1).padStart(2, '0')}</span>
      ${hyperlink(p.url, p.title)} <span class="idea-reference-year">${text(p.year)}</span></div>
    <p><b>前人已做：</b>${text(p.did)}</p><p><b>仍需确认：</b>${text(p.still)}</p>
  </div>`).join('');
  const novelty = (item, index) => `<div class="idea-novelty">
    <span class="idea-novelty-index">创新点 ${String(index + 1).padStart(2,'0')}</span>
    <div><strong>${text(item.title)}</strong><p><b>拟采用机制：</b>${text(item.mechanism)}</p>
    <p><b>希望形成的贡献：</b>${text(item.contribution)}</p></div>
  </div>`;
  const resources = list => (list || []).map(x => `<div class="idea-resource"><strong>${hyperlink(x.url, x.name)}</strong><p>${text(x.note)}</p></div>`).join('');
  const latest = (evidence, item) => {
    const records = evidence?.topics?.[item.id]?.papers || [];
    const checkDate = evidence?.checked_at ? evidence.checked_at.slice(0,10) : '待首次周更';
    const caption = '<strong>本周新增证据（自动匹配，尚未全文核查）</strong>';
    if (!records.length) return `<div class="idea-evidence"><div class="idea-evidence-heading">${caption}<span>${text(checkDate)}</span></div>
      <p>本次尚无新的高相关论文候选。现有科学问题与创新假设不因更新频率而自动改写。</p></div>`;
    return `<div class="idea-evidence"><div class="idea-evidence-heading">${caption}<span>${text(checkDate)}</span></div>
      <ol>${records.map(x => `<li>${hyperlink(x.url,x.title)}<span class="idea-evidence-meta">${text(x.date)} · ${text(x.venue)} · 自动匹配，未审全文</span></li>`).join('')}</ol>
      <p>匹配到相关文献不等于已有研究解决了该问题；需检验具体问题定义、监督信号与评价协议。</p></div>`;
  };
  function renderIdea(item, i, evidence) {
    return `<article class="innovation-card" id="idea-${esc(item.id)}">
      <div class="innovation-card-head"><span class="innovation-number">${String(i + 1).padStart(2,'0')}</span>
        <span class="innovation-track">${text(item.track)}</span><span class="innovation-priority">${text(item.priority)}</span></div>
      <h3>${text(item.title)}</h3>
      <div class="idea-paper-tag"><span>独立小论文</span><span>高水平期刊目标 · 需实验证实</span></div>
      <p class="innovation-question">${text(item.question)}</p>
      <div class="idea-scope"><strong>单篇论文边界</strong><p>${text(item.paper_scope)}</p></div>
      <div class="innovation-summary"><span>已有相关研究 ${(item.prior || []).length} 篇</span>
        <span>候选创新点 ${(item.novelties || []).length} 项</span>
        <span>1个核心问题 · 最小实验闭环</span></div>
      <div class="innovation-thesis"><strong>论文的核心可证伪主张</strong><p>${text(item.core_claim)}</p></div>
      <div class="innovation-short-novelties">${(item.novelties || []).map((n, j) => `<div><span>${j + 1}</span>${text(n.title)}</div>`).join('')}</div>
      <details class="innovation-details"><summary><span>查看完整创新论证、必做实验与投稿风险</span><span class="innovation-chevron" aria-hidden="true">⌄</span></summary>
        <div class="innovation-expanded">
          <section><h4>01 · 单篇论文定位</h4><p><b>英文拟题：</b>${text(item.paper_title_en)}</p><p><b>论文范围：</b>${text(item.scope_size)}</p><p><b>研究假设：</b>${text(item.hypothesis)}</p><p><b>为何值得研究：</b>${text(item.why_deep)}</p></section>
          <section><h4>02 · 已有研究：真正解决了什么？</h4>${refs(item.prior)}<p><b>尚待核验的缺口：</b>${text(item.gap)}</p></section>
          <section><h4>03 · 2–3 个相互支撑的核心创新点</h4>${(item.novelties || []).map(novelty).join('')}</section>
          <section><h4>04 · 真实数据与最小可投稿实验</h4><div class="idea-resource-list">${resources(item.data)}</div>
            <p><b>必要基线与消融：</b>${text(item.validation)}</p><div class="idea-killer"><strong>决定能否达到高水平期刊证据要求的关键实验</strong><p>${text(item.key_experiment)}</p></div></section>
          <section><h4>05 · 顶刊目标、止损条件与已有工作重叠</h4><p><b>止损规则：</b>${text(item.stop_condition)}</p><p><b>必须先核查：</b>${text((item.required_checks || []).join("；"))}</p><p><b>已有工作重叠风险：</b>${text(item.overlap)}</p><p><b>候选投稿方向：</b>${text(item.venue_fit)}</p><p><b>可行性：</b>${text(item.feasibility)}</p></section>
          ${latest(evidence, item)}
        </div>
      </details>
    </article>`;
  }
  async function readJson(path, optional=false) {
    try {
      const response=await fetch(path,{cache:'no-store'});
      if(!response.ok)throw new Error('HTTP '+response.status);
      return await response.json();
    } catch(e) {
      if(optional)return null;
      throw e;
    }
  }
  async function load() {
    try {
      const [ideas, evidence] = await Promise.all([
        readJson('research-ideas.json'), readJson('idea-evidence.json',true)
      ]);
      if(!Array.isArray(ideas.ideas))throw new Error('候选选题文件缺少 ideas');
      container.innerHTML = ideas.ideas.map((x,i) => renderIdea(x,i,evidence)).join('');
      const last = (evidence?.checked_at||'').slice(0,10) || '首次周更尚未执行';
      state.textContent = `研究问题上次整理：${ideas.reviewed_on || '待核验'}　·　自动文献证据最近检查：${last}　·　每周六北京时间 10:00`;
    } catch(e) {
      container.innerHTML='<div class="innovation-loading">暂时无法读取选题库。请检查研究数据文件和 GitHub Pages 部署状态。</div>';
      state.textContent='选题库加载失败，不影响原有论文收集和收藏功能。';
    }
  }
  if(nav)nav.addEventListener('click',()=>{
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('innovationLab')?.scrollIntoView({behavior:'smooth',block:'start'});
  });
  load();
})();
