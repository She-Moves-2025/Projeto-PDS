document.addEventListener('DOMContentLoaded', function() {
  const tabLocal = document.getElementById('tab-local');
  const tabEspecialidade = document.getElementById('tab-especialidade');
  const contentLocal = document.getElementById('content-local');
  const contentEspecialidade = document.getElementById('content-especialidade');
  const buscarBtn = document.getElementById('buscar-btn');
  const estadoSelect = document.getElementById('estado');
  const cidadeSelect = document.getElementById('cidade');
  const bairroSelect = document.getElementById('bairro');

  // Tabs
  tabLocal.onclick = function() {
    this.classList.add('active');
    tabEspecialidade.classList.remove('active');
    contentLocal.style.display = '';
    contentEspecialidade.style.display = 'none';
    validarFormulario();
  }

  tabEspecialidade.onclick = function() {
    this.classList.add('active');
    tabLocal.classList.remove('active');
    contentLocal.style.display = 'none';
    contentEspecialidade.style.display = '';
    validarFormulario();
  }

  // Carrega estados
  fetch('/api/estados')
    .then(res => res.json())
    .then(estados => {
      estados.forEach(e => {
        estadoSelect.innerHTML += `<option value="${e.nome}">${e.nome} (${e.sigla})</option>`;
      });
    });

  // Carrega cidades
  estadoSelect.onchange = function() {
    const estadoNome = this.value;
    const estadoObj = JSON.parse(estadoSelect.options[estadoSelect.selectedIndex].dataset.obj || '{}');
    cidadeSelect.innerHTML = '<option value="">Cidade</option>';
    bairroSelect.innerHTML = '<option value="">Bairro</option>';
    bairroSelect.disabled = true;
    if (estadoNome) {
      cidadeSelect.disabled = false;
      // Buscar ID do estado pelo nome e carregar cidades
      fetch('/api/estados')
        .then(res => res.json())
        .then(estados => {
          const estado = estados.find(e => e.nome === estadoNome);
          if (estado) {
            return fetch(`/api/cidades/${estado.id}`);
          }
        })
        .then(res => res.json())
        .then(cidades => {
          cidades.forEach(c => {
            cidadeSelect.innerHTML += `<option value="${c.nome}" data-id="${c.id}">${c.nome}</option>`;
          });
        });
    } else {
      cidadeSelect.disabled = true;
    }
    validarFormulario();
  };

  // Carrega bairros
  cidadeSelect.onchange = function() {
    const cidadeId = this.options[this.selectedIndex].dataset.id;
    bairroSelect.innerHTML = '<option value="">Bairro</option>';
    if (cidadeId) {
      bairroSelect.disabled = false;
      fetch(`/api/bairros/${cidadeId}`)
        .then(res => res.json())
        .then(bairros => {
          bairros.forEach(b => {
            bairroSelect.innerHTML += `<option value="${b.name}">${b.name}</option>`;
          });
        });
    } else {
      bairroSelect.disabled = true;
    }
    validarFormulario();
  };

  // Validação do formulário
  function validarFormulario() {
    const modalidadeSelecionada = document.querySelector('input[name="modalidade"]:checked');
    const localCompleto = estadoSelect.value && cidadeSelect.value && bairroSelect.value;
    
    if (modalidadeSelecionada && localCompleto) {
      buscarBtn.disabled = false;
    } else {
      buscarBtn.disabled = true;
    }
  }

  // Validar ao selecionar modalidade
  document.querySelectorAll('input[name="modalidade"]').forEach(radio => {
    radio.addEventListener('change', validarFormulario);
  });

  // Validar ao mudar selects
  bairroSelect.addEventListener('change', validarFormulario);
});
