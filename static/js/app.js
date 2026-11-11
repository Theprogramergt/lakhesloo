const $ = (s) => document.querySelector(s);
let documentId = null;
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const renderText = (value) => escapeHtml(value).replace(/\n/g, '<br>');
async function api(url, options) {
  const response = await fetch(url, {headers: {'Content-Type': 'application/json'}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}
const fileInput = $('#file-input'), dropZone = $('#drop-zone');
dropZone.onclick = () => fileInput.click();
fileInput.onchange = () => { if (fileInput.files[0]) dropZone.querySelector('h2').textContent = fileInput.files[0].name; };
['dragenter','dragover'].forEach((event) => dropZone.addEventListener(event, (e) => {e.preventDefault();dropZone.classList.add('drag');}));
['dragleave','drop'].forEach((event) => dropZone.addEventListener(event, (e) => {e.preventDefault();dropZone.classList.remove('drag');}));
dropZone.addEventListener('drop', (e) => {fileInput.files = e.dataTransfer.files; fileInput.onchange();});
$('#upload-form').onsubmit = async (e) => {
  e.preventDefault(); const file = fileInput.files[0]; if (!file) return;
  $('#upload-status').textContent = 'Extracting every page…';
  try {
    const form = new FormData(); form.append('file', file);
    const response = await fetch('/api/documents', {method:'POST', body:form}); const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    documentId = data.id; $('#document-name').textContent = data.filename;
    $('#document-meta').textContent = `${data.page_count} pages · ${data.extracted_pages} text pages`;
    $('#landing').classList.add('hidden'); $('#workspace').classList.remove('hidden');
    if (data.warnings.length) $('#summary-result').innerHTML = `<p class="status">${escapeHtml(data.warnings.join(' '))}</p>`;
  } catch (error) { $('#upload-status').textContent = error.message; }
};
$('#new-document').onclick = () => location.reload();
document.querySelectorAll('.tab').forEach((button) => button.onclick = () => {
  document.querySelectorAll('.tab,.panel').forEach((el) => el.classList.remove('active'));
  button.classList.add('active'); $(`#${button.dataset.tab}`).classList.add('active');
});
async function loadSummary(style) {
  $('#summary-result').className = 'result empty'; $('#summary-result').textContent = 'Reading the document with Gemini…';
  try { const data = await api(`/api/documents/${documentId}/summary`, {method:'POST', body:JSON.stringify({style})}); $('#summary-result').className = 'result'; $('#summary-result').innerHTML = formatAiText(data.content); typesetMath(); }
  catch (error) { $('#summary-result').textContent = error.message; }
}
function formatAiText(text) {
  const lines = String(text).replace(/\r/g, '').split('\n');
  return lines.map((line) => {
    const clean = line.replace(/^\s*[-*_]{3,}\s*$/, '').trim();
    if (!clean) return '';
    const heading = clean.match(/^#{1,6}\s+(.+)$/);
    if (heading) {
      const level = Math.min(heading[0].match(/^#+/)[0].length, 4);
      return `<h${level}>${renderInline(heading[1])}</h${level}>`;
    }
    const bullet = clean.match(/^(?:[-*+]|\d+\.)\s+(.+)$/);
    if (bullet) return `<li>${renderInline(bullet[1])}</li>`;
    return `<p>${renderInline(clean)}</p>`;
  }).join('');
}
function renderInline(text) {
  const formulas = [];
  let source = String(text);
  const trimmed = source.trim();
  if (looksLikeBareFormula(trimmed)) {
    source = `\\(${trimmed}\\)`;
  }
  source = source.replace(
    /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\\\([\s\S]+?\\\)|\\\[[\s\S]+?\\\])/g,
    (formula) => {
      if (formula.startsWith('$$') && formula.endsWith('$$')) {
        formula = `\\[${formula.slice(2, -2)}\\]`;
      } else if (formula.startsWith('$') && formula.endsWith('$')) {
        formula = `\\(${formula.slice(1, -1)}\\)`;
      }
      formulas.push(formula);
      return `@@FORMULA_${formulas.length - 1}@@`;
    }
  );
  const cleaned = stripMarkdown(source)
    .replace(/^\*+\s*/, '')
    .replace(/\s+\*+$/, '');
  return escapeHtml(cleaned).replace(/@@FORMULA_(\d+)@@/g, (_match, index) => formulas[index]);
}
function looksLikeBareFormula(text) {
  if (!text || text.includes('\\(') || text.includes('\\[')) return false;
  const hasLatexCommand = /\\(?:forall|exists|in|notin|ge|le|neq|approx|frac|sqrt|lambda|alpha|beta|gamma|sum|int|operatorname|text|mathbf|hat|bar)\b/.test(text);
  const hasLatexStructure = /[_^{}]|\\[a-zA-Z]+/.test(text);
  return hasLatexCommand || (hasLatexStructure && !/[.!?]\s+[A-Z]/.test(text));
}
function stripMarkdown(text) {
  return String(text)
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    .replace(/(^|[\s(])_([^_]+)_/g, '$1$2')
    .replace(/(^|[\s:])\*+(?=\S)/g, '$1');
}
function typesetMath() {
  if (window.MathJax && typeof MathJax.typesetPromise === 'function') {
    MathJax.typesetPromise();
  } else {
    window.setTimeout(typesetMath, 100);
  }
}
function markedLite(text) { return formatAiText(text); }
document.querySelectorAll('[data-style]').forEach((button) => button.onclick = () => {document.querySelectorAll('[data-style]').forEach((b) => b.classList.remove('active'));button.classList.add('active');loadSummary(button.dataset.style);});
$('#generate-quiz').onclick = async () => {
  $('#quiz-result').className = 'result empty'; $('#quiz-result').textContent = 'Generating questions…';
  try { const data = await api(`/api/documents/${documentId}/quiz`, {method:'POST',body:JSON.stringify({difficulty:$('#difficulty').value,count:$('#question-count').value})}); renderQuiz(data.questions); }
  catch (error) { $('#quiz-result').textContent = error.message; }
};
function renderQuiz(questions) {
  $('#quiz-result').className = 'result'; $('#quiz-result').innerHTML = questions.map((q,i) => `<div class="question"><strong>${i+1}. ${formatAiText(q.question)}</strong>${q.options.map((o,j)=>`<label><input type="radio" name="q${i}" value="${j}"> ${formatAiText(o)}</label>`).join('')}<small class="explanation hidden" data-answer="${q.answer}">Answer: ${formatAiText(q.explanation)}</small></div>`).join('') + '<button id="submit-quiz" class="primary">Check answers</button>';
  typesetMath();
  $('#submit-quiz').onclick = () => {let score=0; questions.forEach((q,i)=>{const picked=document.querySelector(`input[name="q${i}"]:checked`);const note=document.querySelectorAll('.explanation')[i];note.classList.remove('hidden');if(picked && Number(picked.value)===q.answer) score++;});$('#submit-quiz').textContent=`Score: ${score}/${questions.length}`;typesetMath();};
}
$('#chat-form').onsubmit = async (e) => {e.preventDefault();const input=$('#chat-input'), question=input.value.trim();if(!question)return;$('#chat-messages').insertAdjacentHTML('beforeend',`<div class="message user">${escapeHtml(question)}</div>`);input.value='';const pending=document.createElement('div');pending.className='message assistant';pending.textContent='Thinking…';$('#chat-messages').append(pending);try{const data=await api(`/api/documents/${documentId}/chat`,{method:'POST',body:JSON.stringify({question})});pending.innerHTML=`${formatAiText(data.answer)}<br><small>Pages: ${data.pages.join(', ')||'not specified'}</small>`;typesetMath();}catch(error){pending.textContent=error.message;}pending.scrollIntoView();};
