import json
import os


class ConfiguracaoTributaria:
    """Gerencia as configurações tributárias do simulador."""

    def __init__(self):
        # Alíquotas base do IVA Dual conforme Art. 12º, LC 214/2025
        self.aliquotas_base = {
            "CBS": 0.088,  # 8,8%
            "IBS": 0.177  # 17,7%
        }

        # Percentual progressivo (2026-2033) - Anexo III, LC 214/2025
        self.fase_transicao = dict()
        self.fase_transicao[2026] = 0.10  # 10% de implementação
        self.fase_transicao[2027] = 0.25  # 25% de implementação
        self.fase_transicao[2028] = 0.40  # 40% de implementação
        self.fase_transicao[2029] = 0.60  # 60% de implementação
        self.fase_transicao[2030] = 0.80  # 80% de implementação
        self.fase_transicao[2031] = 0.90  # 90% de implementação
        self.fase_transicao[2032] = 0.95  # 95% de implementação
        self.fase_transicao[2033] = 1.00  # Implementação completa

        # Setores com alíquotas diferenciadas - Art. 18º, §§ 2º-5º
        self.setores_especiais = {
            "padrao": {"IBS": 0.177, "reducao_CBS": 0.0},
            "educacao": {"IBS": 0.125, "reducao_CBS": 0.40},  # Educação básica
            "saude": {"IBS": 0.145, "reducao_CBS": 0.30},  # Serviços médicos
            "alimentos": {"IBS": 0.120, "reducao_CBS": 0.25},  # Alimentos básicos
            "transporte": {"IBS": 0.150, "reducao_CBS": 0.20}  # Transporte coletivo
        }

        # Produtos com alíquota zero (Anexos I e XV)
        self.produtos_aliquota_zero = [
            "Arroz", "Feijão", "Leite", "Pão", "Frutas", "Hortaliças"
        ]

        # Limite para enquadramento no Simples Nacional - Art. 34º
        self.limite_simples = 4_800_000

        # Regras de crédito - Art. 29º
        self.regras_credito = {
            "normal": 1.0,  # Crédito integral
            "simples": 0.20,  # Limitado a 20% do valor da compra
            "rural": 0.60,  # Produtor rural: 60% sobre CBS
            "importacoes": {"IBS": 1.0, "CBS": 0.50}  # Importações: 100% IBS, 50% CBS
        }

        # Configurações para os impostos atuais
        self.impostos_atuais = {
            "PIS": 0.0165,  # 1,65%
            "COFINS": 0.076,  # 7,6%
            "IPI": {
                "padrao": 0.10,  # 10% (média, varia por produto)
                "industria": 0.15  # 15% para indústria
            },
            "ICMS": {
                "padrao": 0.19,  # 19% (média estadual)
                "comercio": 0.19,  # Comércio
                "industria": 0.19,  # Indústria
                "servicos": 0.19  # Serviços (quando aplicável)
            },
            "ISS": {
                "padrao": 0.05,  # 5% (média municipal)
                "servicos": 0.05  # Serviços
            }
        }

        # Configurações para ICMS e incentivos fiscais
        self.icms_config = {
            "aliquota_entrada": 0.19,  # 19% padrão
            "aliquota_saida": 0.19,  # 19% padrão
            "incentivos_saida": [],  # Lista de dicionários para incentivos de saída
            "incentivos_entrada": [],  # Lista de dicionários para incentivos de entrada
            "incentivos_apuracao": []  # Lista de dicionários para incentivos de apuração
        }

        # Estrutura de exemplo para incentivos
        self.incentivo_template = {
            "tipo": "Nenhum",  # Tipos atualizados conforme necessário
            "descricao": "",  # Descrição do incentivo (ex: "PRODEPE", "Fomentar", etc)
            "percentual": 0.0,  # Percentual do incentivo
            "percentual_operacoes": 1.0,  # Percentual das operações que recebem o incentivo
            "aplicavel_entradas": False,  # Se o incentivo se aplica às entradas
            "aplicavel_saidas": False,  # Se o incentivo se aplica às saídas
            "aplicavel_apuracao": False  # Se o incentivo se aplica à apuração
        }

        # Cronograma de redução progressiva dos impostos durante a transição
        self.reducao_impostos_transicao = {
            2026: {"PIS": 0.0, "COFINS": 0.0, "IPI": 0.0, "ICMS": 0.0, "ISS": 0.0},
            2027: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.0, "ICMS": 0.0, "ISS": 0.0},
            2028: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.3, "ICMS": 0.33, "ISS": 0.40},
            2029: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.6, "ICMS": 0.56, "ISS": 0.70},
            2030: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.8, "ICMS": 0.70, "ISS": 0.80},
            2031: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.9, "ICMS": 0.80, "ISS": 0.90},
            2032: {"PIS": 1.0, "COFINS": 1.0, "IPI": 0.95, "ICMS": 0.95, "ISS": 0.95},
            2033: {"PIS": 1.0, "COFINS": 1.0, "IPI": 1.0, "ICMS": 1.0, "ISS": 1.0}
        }

        # Configurações para incentivos fiscais
        self.incentivo_fiscal_icms = 0.0  # Percentual de redução (0.0 a 1.0)

        # Regras de créditos cruzados
        self.creditos_cruzados = {
            2028: {"IBS_para_ICMS": 0.40},  # 40% do IBS pode compensar ICMS
            2029: {"IBS_para_ICMS": 0.50},  # 50% do IBS pode compensar ICMS
            2030: {"IBS_para_ICMS": 0.60},
            2031: {"IBS_para_ICMS": 0.70},
            2032: {"IBS_para_ICMS": 0.80}
        }

    def carregar_configuracoes(self, arquivo=None):
        """Carrega configurações de um arquivo JSON, se existir."""
        if arquivo and os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "aliquotas_base" in config:
                        self.aliquotas_base = config["aliquotas_base"]
                    if "fase_transicao" in config:
                        self.fase_transicao = config["fase_transicao"]
                    if "setores_especiais" in config:
                        self.setores_especiais = config["setores_especiais"]
                return True
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
                return False
        return False

    def salvar_configuracoes(self, arquivo):
        """Salva as configurações atuais em um arquivo JSON."""
        try:
            config = {
                "aliquotas_base": self.aliquotas_base,
                "fase_transicao": self.fase_transicao,
                "setores_especiais": self.setores_especiais,
                "limite_simples": self.limite_simples,
                "regras_credito": self.regras_credito
            }
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
            return False

    def obter_aliquotas_efetivas(self, setor, ano):
        """Calcula as alíquotas efetivas considerando o setor e o ano."""
        # Obter fator de implementação para o ano
        fator_implementacao = self.fase_transicao.get(ano, 1.0)

        # Obter regras específicas do setor
        regras_setor = self.setores_especiais.get(setor, self.setores_especiais["padrao"])

        # Calcular alíquotas efetivas
        cbs_efetivo = self.aliquotas_base["CBS"] * (1 - regras_setor["reducao_CBS"]) * fator_implementacao
        ibs_efetivo = regras_setor["IBS"] * fator_implementacao

        return {
            "CBS": cbs_efetivo,
            "IBS": ibs_efetivo,
            "total": cbs_efetivo + ibs_efetivo
        }