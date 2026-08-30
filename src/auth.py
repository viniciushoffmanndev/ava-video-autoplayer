def realizar_login(page, url, cpf, senha):
    print("-> Efetuando Login...")
    page.goto(url)

    page.fill("input[type='text'], input[name='login'], input[name='usuario']", cpf)
    page.fill("input[type='password']", senha)
    page.click("button:has-text('ENTRAR'), input[type='submit']")
    page.wait_for_timeout(3000)
