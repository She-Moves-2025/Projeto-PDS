document.addEventListener('DOMContentLoaded', function() {
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
});
