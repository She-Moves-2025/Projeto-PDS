document.addEventListener('DOMContentLoaded', () =>{
  const form = document.getElementById('login-form');
  const emailInput = document.getElementById('email');
  const senhaInput = document.getElementById('senha');
  const emailError = document.getElementById('email-error');
  const senhaError = document.getElementById('senha-error');

  // Checklist elements
  const checkLength = document.getElementById('check-length');
  const checkNumber = document.getElementById('check-number');
  const checkSpecial = document.getElementById('check-special');

  // Admin credentials
  const adminEmail = 'admin@master';
  const adminSenha = '010203';

  function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function hasNumber(str) {
    return /\d/.test(str);
  }

  function hasSpecialChar(str) {
    return /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(str);
  }

  function updatePasswordChecklist(senha) {
    // 8+ chars
    if (senha.length >= 8) {
      checkLength.classList.add('valid');
    } else {
      checkLength.classList.remove('valid');
    }
    // number
    if (hasNumber(senha)) {
      checkNumber.classList.add('valid');
    } else {
      checkNumber.classList.remove('valid');
    }
    // special char
    if (hasSpecialChar(senha)) {
      checkSpecial.classList.add('valid');
    } else {
      checkSpecial.classList.remove('valid');
    }
  }

  senhaInput.addEventListener('input', function() {
    updatePasswordChecklist(senhaInput.value);
    senhaError.textContent = '';
  });

  emailInput.addEventListener('input', function() {
    emailError.textContent = '';
  });

  form.addEventListener('submit', function(e) {
    let valid = true;
    emailError.textContent = '';
    senhaError.textContent = '';

    // Exceção para admin
    if (emailInput.value === adminEmail && senhaInput.value === adminSenha) {
      return; // Permite o envio do formulário normalmente
    }

    // Validação do e-mail
    if (!validateEmail(emailInput.value)) {
      emailError.textContent = 'Digite um e-mail válido.';
      valid = false;
    }

    // Validação da senha
    let senha = senhaInput.value;
    if (senha.length < 8) {
      senhaError.textContent = 'A senha deve ter pelo menos 8 caracteres.';
      valid = false;
    } else if (!hasNumber(senha)) {
      senhaError.textContent = 'A senha deve ter pelo menos um número.';
      valid = false;
    } else if (!hasSpecialChar(senha)) {
      senhaError.textContent = 'A senha deve ter pelo menos um caractere especial.';
      valid = false;
    }

    if (!valid) {
      e.preventDefault();
    }
  });

  const cpfInput = document.getElementById("cpf");
  const crefInput = document.getElementById("cref");

  if (cpfInput) {
    const aplicarMascaraCPF = (valor) => {
      
      let v = valor.replace(/\D/g, "").slice(0, 11);

      v = v.replace(/(\d{3})(\d)/, "$1.$2");
      v = v.replace(/(\d{3})(\d)/, "$1.$2");
      v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
      return v;
    };

    cpfInput.addEventListener("input", (e) => {
      e.target.value = aplicarMascaraCPF(e.target.value);
    });

    cpfInput.addEventListener("paste", (e) => {
      e.preventDefault();
      const texto = (e.clipboardData || window.clipboardData).getData("text");
      cpfInput.value = aplicarMascaraCPF(texto);
    });
  }

  document.getElementById('login-form').addEventListener('submit', function (e) {
    let cpfInput = document.getElementById("cpf");
    cpfInput.value = cpfInput.value.replace(/\D/g, "");
});

  if (crefInput) {
    const aplicarMascaraCref = (valor) => {
      
      let v = valor.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();

      v = v.replace(/^(\d{6})([A-Z])/, "$1-$2");
      v = v.replace(/^(\d{6}-[A-Z])([A-Z]{2})/, "$1/$2");
      return v;
    };

    crefInput.addEventListener("input", (e) => {
      e.target.value = aplicarMascaraCref(e.target.value);
    });

    crefInput.addEventListener("paste", (e) => {
      e.preventDefault();
      const texto = (e.clipboardData || window.clipboardData).getData("text");
      crefInput.value = aplicarMascaraCref(texto);
    });
  }
});

document.getElementById('olho').addEventListener('mousedown', function() {
  document.getElementById('senha').type = 'text';
});

document.getElementById('olho').addEventListener('mouseup', function() {
  document.getElementById('senha').type = 'password';
});

// Para que o password não fique exposto apos mover a imagem.
document.getElementById('olho').addEventListener('mousemove', function() {
  document.getElementById('senha').type = 'password';
});