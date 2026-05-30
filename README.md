# 🚀 CI/CD no Microsoft Fabric com Azure DevOps

> Workshop prático conduzido por **Sidney** e **Alison** — comunidade Power BI / Fabric

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Conceitos Fundamentais](#conceitos-fundamentais)
- [Arquitetura](#arquitetura)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Fluxo de Trabalho Git](#fluxo-de-trabalho-git)
- [Pipelines CI/CD](#pipelines-cicd)
- [Boas Práticas](#boas-práticas)
- [Troubleshooting](#troubleshooting)
- [Recursos e Referências](#recursos-e-referências)

---

## Visão Geral

Este repositório reúne os conceitos, templates e práticas abordados no workshop sobre **CI/CD no Microsoft Fabric**, com foco em:

- Automação de deployments entre ambientes (Dev → QA → Prod)
- Versionamento de artefatos do Fabric via Git
- Integração com **Azure DevOps** e a biblioteca **PyFabricOps**
- Gestão segura de credenciais com **Azure Key Vault**

O objetivo central é ensinar os fundamentos de DevOps aplicados ao ecossistema Microsoft Fabric, de forma que as práticas possam ser adaptadas a qualquer empresa, independentemente das ferramentas específicas utilizadas.

---

## Pré-requisitos

| Requisito | Observação |
|---|---|
| Subscrição Azure ativa | Trial (60 dias) ou licença permanente |
| Conta Azure DevOps | Organização e projeto criados |
| Microsoft Fabric (capacidade F ou Trial) | Recomendado F64+ para produção |
| Conhecimento básico de Git | Clone, commit, branch, merge |
| Python (opcional) | Necessário apenas para uso local da PyFabricOps |
| VS Code (opcional) | Recomendado para trabalho local |

---

## Conceitos Fundamentais

### DevOps
> Conjunto de **pessoas**, **processos** e **produtos** que habilitam a entrega contínua de valor.

### CI/CD
- **CI (Integração Contínua):** Prática de integrar código frequentemente, com validações automáticas a cada merge.
- **CD (Entrega Contínua):** Automatização do processo de deploy entre ambientes.

### Git vs GitHub/Azure DevOps
| | Git | GitHub / Azure DevOps / GitLab |
|---|---|---|
| O que é | Sistema de versionamento local | Plataforma de colaboração na nuvem |
| Roda onde | Na máquina do desenvolvedor | Na web |
| Alternativa self-hosted | — | GitLab (ideal para redes privadas) |

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Azure DevOps                         │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────────┐ │
│  │  Boards  │   │   Repos  │   │  Pipelines (YAML)   │ │
│  └──────────┘   └────┬─────┘   └──────────┬──────────┘ │
└───────────────────────┼───────────────────┼─────────────┘
                        │                   │
              ┌─────────▼─────────┐         │
              │   Microsoft Fabric│         │ trigger (merge)
              │                   │         │
              │  [Dev Workspace]  │◄────────┘
              │  [QA  Workspace]  │  PyFabricOps 
              │  [Prod Workspace] │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │   Azure Key Vault  │
              │  (secrets/creds)   │
              └────────────────────┘
```

### Camadas de dados (Lakehouse)

```
Ingestão → [Bronze] → [Silver] → [Gold] → Modelo Semântico → Power BI
```

| Camada | Descrição |
|---|---|
| **Bronze** | Dados brutos, sem transformação |
| **Silver** | Dados limpos e padronizados |
| **Gold** | Dados prontos para consumo analítico |

---

## Configuração do Ambiente

### 1. Registro de Aplicação (Service Principal)

No portal Azure (`portal.azure.com`):

1. Acesse **Azure Active Directory → App Registrations → New Registration**
2. Anote: `Application (Client) ID`, `Object ID`, `Directory (Tenant) ID`
3. Em **Certificates & Secrets**, crie um novo secret (validade máx. 24 meses)
4. Adicione o Service Principal como membro do Workspace no Fabric com permissão de **Contributor**

> ⚠️ **Atenção:** Implemente rotação automática de secrets. Não gerencie manualmente.

### 2. Azure Key Vault

```bash
# Custo aproximado: ~R$ 1,00/mês por vault
# Recomendação de região: mesma região do Fabric (Brasil Sul) para produção
```

Permissões necessárias no Key Vault:

| Role | Permissão |
|---|---|
| `Key Vault Secrets User` | Leitura de secrets (para pipelines) |
| `Key Vault Secrets Officer` | Criação/alteração de secrets (para admins) |

### 3. Integração Git no Fabric Workspace

1. No Workspace → **Workspace Settings → Git Integration**
2. Conecte ao repositório Azure DevOps
3. Selecione a branch correspondente ao ambiente (`dev`, `main`)

> ⚠️ **Regra crítica:** Ambientes de **produção** nunca devem estar conectados à branch `dev`.

### 4. Variáveis de Ambiente (Library Variables)

Configure no Azure DevOps em **Pipelines → Library**:

```yaml
# Exemplo de variáveis por ambiente
LAKEHOUSE_ID: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
DATABASE_CONNECTION: "Server=...;Database=..."
WORKSPACE_ID: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

> ⚠️ **Nunca armazene** senhas ou client secrets nas variáveis do Fabric. Use o Key Vault.

---

## Fluxo de Trabalho Git

### Estrutura de Branches

```
main (produção)
│
├── dev (desenvolvimento integrado)
│   ├── feature/ingestao-vendas
│   ├── feature/modelo-financeiro
│   └── feature/pipeline-qualidade
│
└── hotfix/correcao-critica (direto para main, quando necessário)
```

### Comandos Essenciais

```bash
# Clonar repositório
git clone <url-do-repositorio>

# Criar e trocar para nova branch de feature
git checkout -b feature/nome-da-feature

# Verificar status das mudanças
git status

# Adicionar arquivos ao stage
git add .

# Commitar com Conventional Commits
git commit -m "feat: adiciona pipeline de ingestão de vendas"
git commit -m "fix: corrige ID do lakehouse no workspace dev"
git commit -m "docs: atualiza readme com instruções de deploy"

# Enviar branch para o repositório remoto
git push origin feature/nome-da-feature

# Atualizar branch local com mudanças remotas
git pull origin dev

# Merge de feature para dev (via Pull Request — não faça direto!)
git checkout dev
git merge feature/nome-da-feature
```

### Conventional Commits

| Prefixo | Uso |
|---|---|
| `feat:` | Nova funcionalidade |
| `fix:` | Correção de bug |
| `docs:` | Documentação |
| `refactor:` | Refatoração sem mudança de comportamento |
| `test:` | Adição ou correção de testes |
| `chore:` | Tarefas de manutenção (ex: atualizar dependências) |

### Recuperação de Dados

```bash
# Desfazer último commit (mantendo as mudanças locais)
git reset --soft HEAD~1

# Reverter um commit específico (seguro para branches compartilhadas)
git revert <hash-do-commit>

# Ver histórico de commits
git log --oneline

# Trazer mudanças de uma branch para outra (cherry-pick)
git cherry-pick <hash-do-commit>
```

---

## Pipelines CI/CD

### Estrutura do arquivo YAML

```yaml
trigger:
  branches:
    include:
      - main   # Deploy para produção apenas no merge para main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: fabric-prod-variables   # Library criada no Azure DevOps

stages:
  - stage: Validate
    jobs:
      - job: RunTests
        steps:
          - script: |
              pip install pyfabricops
              python run_tests.py
            displayName: 'Executar testes de qualidade'

  - stage: Deploy
    dependsOn: Validate
    condition: succeeded()
    jobs:
      - job: DeployToProduction
        steps:
          - script: |
              python deploy.py --env prod
            displayName: 'Deploy para Produção'
```

### Quando usar cada abordagem de deploy

| Método | Quando usar | Limitações |
|---|---|---|
| **Deployment Pipeline (Fabric)** | Projetos simples, hot fixes manuais | Não troca parâmetros de Direct Lake no deploy; não versiona Dataflow G1 |
| **Azure Pipeline (YAML)** | Automação completa, troca de variáveis entre ambientes | Requer configuração mais elaborada |
| **PyFabricOps / Yemo** | Deploy seletivo, modelos semânticos, automação via API | Curva de aprendizado inicial |

### Dataflow: atenção!

- **Dataflow G1:** Não é versionável no Git. Será descontinuado. Migre para G2.
- **Dataflow G2:** Versionável, melhor performance, menor consumo de capacidade.

---

## Boas Práticas

### Organização de Workspaces

```
✅ Um Workspace por equipe/repositório
✅ Workspaces de Dev descentralizados por área de negócio
✅ Workspace de Produção centralizado e gerenciado pela TI
✅ Apagar Workspaces temporários de feature após o merge

❌ Nunca conectar Prod diretamente à branch dev
❌ Nunca usar funcionalidades em Preview em produção
```

### Segurança

```
✅ Princípio do menor privilégio para todas as permissões
✅ Service Principal ao invés de usuários pessoais para automação
✅ Secrets gerenciados via Key Vault, com rotação automática
✅ Arquivos sensíveis listados no .gitignore

❌ Nunca armazenar senhas ou client secrets em variáveis do Fabric
❌ Nunca comitar arquivos .env ou cache do Power BI
```

### .gitignore recomendado para projetos Fabric/Power BI

```gitignore
# Variáveis de ambiente locais
.env
*.env

# Cache do Power BI Desktop
*.pbix
**/.pbi/

# Arquivos de sistema
.DS_Store
Thumbs.db

# Pastas de dependências locais
__pycache__/
*.pyc
.venv/
```

### IDs de Artefatos

> Sempre use **IDs** para referenciar artefatos (Lakehouse, Notebooks, etc.), **nunca nomes**.  
> Nomes podem mudar entre ambientes; IDs são únicos e estáveis.

```python
# ✅ Correto
lakehouse_id = os.getenv("LAKEHOUSE_ID")

# ❌ Evitar
lakehouse_name = "lakehouse_producao"
```

### Pull Requests

- Toda mudança para `dev` ou `main` deve passar por **Pull Request**
- Defina ao menos um aprovador para merges em `main`
- Prefira **Squash Merge** para manter o histórico limpo
- Valide testes automatizados antes de aprovar

---

## Troubleshooting

### Artefato não está sendo comitado no Fabric

**Causa provável:** O Service Principal não tem acesso à conexão de dados usada pelo artefato.

**Solução:**
1. Verifique se o Service Principal tem permissão na fonte de dados
2. Confirme se todas as conexões do artefato estão configuradas
3. Verifique as permissões no Key Vault (`Secret User` no mínimo)

---

### IDs incorretos após deploy

**Causa:** IDs de Lakehouse e artefatos mudam entre workspaces.

**Solução:**
1. Após o primeiro deploy, atualize manualmente os IDs nas variáveis de biblioteca
2. No próximo deploy, o pipeline usará os IDs corretos automaticamente

---

### Notebook deletado sem commit

**Solução:**
1. Abra um chamado na Microsoft (possibilidade de recuperação via portal admin)
2. Se havia commit anterior: `git revert` ou `git reset` para restaurar o estado
3. **Prevenção:** Sincronize sempre antes de deletar qualquer artefato

---

### Pipeline não executa automaticamente ao abrir PR

**Solução:** Verifique o trigger no YAML:

```yaml
pr:
  branches:
    include:
      - dev
      - main
```

---

## Recursos e Referências

- 📚 [Documentação oficial Microsoft Fabric](https://learn.microsoft.com/fabric)
- 📚 [Azure DevOps Pipelines](https://learn.microsoft.com/azure/devops/pipelines)
- 📚 [Azure Key Vault](https://learn.microsoft.com/azure/key-vault)
- 🐍 [PyFabricOps (Yemo)](https://github.com) — biblioteca open source desenvolvida por Alison
- 📖 Livro recomendado: **Datamesh** — arquitetura de dados descentralizada
- 🎓 Plataforma do workshop: **Dominando Microsoft Fabric**

---

## Convenções de Nomenclatura

| Artefato | Padrão | Exemplo |
|---|---|---|
| Repositório | `minusculas_com_underscore` | `engenharia_dados_vendas` |
| Branch de feature | `feature/descricao-curta` | `feature/pipeline-nfe` |
| Branch de hotfix | `hotfix/descricao-curta` | `hotfix/correcao-lakehouse-id` |
| Workspace Dev | `[Equipe] - Dev` | `Engenharia - Dev` |
| Workspace Prod | `[Equipe] - Prod` | `Engenharia - Prod` |

---

<div align="center">

**Workshop CI/CD no Microsoft Fabric**  
Conduzido por Sidney e Alison — Comunidade Power BI Brasil

</div>
