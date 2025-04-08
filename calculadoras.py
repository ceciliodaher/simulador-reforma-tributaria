from config import ConfiguracaoTributaria
from utils import formatar_br


class CalculadoraTributosAtuais:
    """Implementa os cálculos dos tributos do sistema atual (PIS, COFINS, ICMS, ISS, IPI)."""

    def __init__(self, configuracao):
        self.config = configuracao
        self.memoria_calculo = {}  # Para armazenar os passos do cálculo

    def calcular_todos_impostos(self, dados, ano):
        """Implementação dos cálculos dos tributos atuais com memória de cálculo."""
        try:
            # Limpar memória de cálculo anterior
            self.memoria_calculo = {
                "PIS": [],
                "COFINS": [],
                "ICMS": [],
                "ISS": [],
                "IPI": [],
                "total": []
            }

            # Obter dados básicos
            faturamento = dados.get("faturamento", 0)
            custos = dados.get("custos_tributaveis", 0)
            setor = dados.get("setor", "padrao")

            # Cálculo do PIS
            aliquota_pis = self.config.impostos_atuais["PIS"]
            self.memoria_calculo["PIS"].append(f"Faturamento: R$ {formatar_br(faturamento)}")
            self.memoria_calculo["PIS"].append(f"Alíquota PIS: {formatar_br(aliquota_pis * 100)}%")

            credito_pis = 0
            if faturamento > 0:
                credito_pis = custos * aliquota_pis
                self.memoria_calculo["PIS"].append(f"Custos tributáveis: R$ {formatar_br(custos)}")
                self.memoria_calculo["PIS"].append(
                    f"Crédito PIS: R$ {formatar_br(custos)} × {formatar_br(aliquota_pis * 100)}% = R$ {formatar_br(credito_pis)}")

            pis_devido = faturamento * aliquota_pis - credito_pis
            self.memoria_calculo["PIS"].append(
                f"PIS bruto: R$ {formatar_br(faturamento)} × {formatar_br(aliquota_pis * 100)}% = R$ {formatar_br(faturamento * aliquota_pis)}")
            self.memoria_calculo["PIS"].append(
                f"PIS devido: R$ {formatar_br(faturamento * aliquota_pis)} - R$ {formatar_br(credito_pis)} = R$ {formatar_br(pis_devido)}")

            # Cálculo do COFINS
            aliquota_cofins = self.config.impostos_atuais["COFINS"]
            self.memoria_calculo["COFINS"].append(f"Faturamento: R$ {formatar_br(faturamento)}")
            self.memoria_calculo["COFINS"].append(f"Alíquota COFINS: {formatar_br(aliquota_cofins * 100)}%")

            credito_cofins = 0
            if faturamento > 0:
                credito_cofins = custos * aliquota_cofins
                self.memoria_calculo["COFINS"].append(f"Custos tributáveis: R$ {formatar_br(custos)}")
                self.memoria_calculo["COFINS"].append(
                    f"Crédito COFINS: R$ {formatar_br(custos)} × {formatar_br(aliquota_cofins * 100)}% = R$ {formatar_br(credito_cofins)}")

            cofins_devido = faturamento * aliquota_cofins - credito_cofins
            self.memoria_calculo["COFINS"].append(
                f"COFINS bruto: R$ {formatar_br(faturamento)} × {formatar_br(aliquota_cofins * 100)}% = R$ {formatar_br(faturamento * aliquota_cofins)}")
            self.memoria_calculo["COFINS"].append(
                f"COFINS devido: R$ {formatar_br(faturamento * aliquota_cofins)} - R$ {formatar_br(credito_cofins)} = R$ {formatar_br(cofins_devido)}")

            # Cálculo do ICMS
            # Substituir o cálculo do ICMS pelo método detalhado
            resultado_icms = self.calcular_icms_detalhado(dados)
            icms_devido = resultado_icms["icms_devido"]

            # Atualizar a memória de cálculo
            self.memoria_calculo["ICMS"] = resultado_icms["memoria_calculo"]

            # Cálculo do ISS (apenas para setores de serviços)
            iss_devido = 0
            if setor in ["servicos", "educacao", "saude"]:
                aliquota_iss = self.config.impostos_atuais["ISS"]["padrao"]
                iss_devido = faturamento * aliquota_iss

                self.memoria_calculo["ISS"].append(f"Faturamento: R$ {formatar_br(faturamento)}")
                self.memoria_calculo["ISS"].append(f"Alíquota ISS: {formatar_br(aliquota_iss * 100)}%")
                self.memoria_calculo["ISS"].append(
                    f"ISS devido: R$ {formatar_br(faturamento)} × {formatar_br(aliquota_iss * 100)}% = R$ {formatar_br(iss_devido)}")
            else:
                self.memoria_calculo["ISS"].append(f"Não aplicável ao setor {setor}")

            # Cálculo do IPI (apenas para indústria)
            ipi_devido = 0
            if setor == "industria":
                aliquota_ipi = self.config.impostos_atuais["IPI"]["industria"]
                fator_credito_ipi = 0.7  # Fator de aproveitamento de crédito do IPI

                credito_ipi = 0
                if faturamento > 0:
                    credito_ipi = custos * aliquota_ipi * fator_credito_ipi

                ipi_devido = faturamento * aliquota_ipi - credito_ipi

                self.memoria_calculo["IPI"].append(f"Faturamento: R$ {formatar_br(faturamento)}")
                self.memoria_calculo["IPI"].append(f"Alíquota IPI: {formatar_br(aliquota_ipi * 100)}%")
                self.memoria_calculo["IPI"].append(f"Custos tributáveis: R$ {formatar_br(custos)}")
                self.memoria_calculo["IPI"].append(f"Fator de aproveitamento: {formatar_br(fator_credito_ipi * 100)}%")
                self.memoria_calculo["IPI"].append(
                    f"Crédito IPI: R$ {formatar_br(custos)} × {formatar_br(aliquota_ipi * 100)}% × {formatar_br(fator_credito_ipi * 100)}% = R$ {formatar_br(credito_ipi)}")
                self.memoria_calculo["IPI"].append(
                    f"IPI bruto: R$ {formatar_br(faturamento)} × {formatar_br(aliquota_ipi * 100)}% = R$ {formatar_br(faturamento * aliquota_ipi)}")
                self.memoria_calculo["IPI"].append(
                    f"IPI devido: R$ {formatar_br(faturamento * aliquota_ipi)} - R$ {formatar_br(credito_ipi)} = R$ {formatar_br(ipi_devido)}")
            else:
                self.memoria_calculo["IPI"].append(f"Não aplicável ao setor {setor}")

            # Cálculo do total
            total = pis_devido + cofins_devido + icms_devido + iss_devido + ipi_devido
            self.memoria_calculo["total"].append(f"Total de tributos = PIS + COFINS + ICMS + ISS + IPI")
            self.memoria_calculo["total"].append(
                f"Total de tributos = R$ {formatar_br(pis_devido)} + R$ {formatar_br(cofins_devido)} + R$ {formatar_br(icms_devido)} + R$ {formatar_br(iss_devido)} + R$ {formatar_br(ipi_devido)}")
            self.memoria_calculo["total"].append(f"Total de tributos = R$ {formatar_br(total)}")

            # Retornar os resultados
            impostos = {
                "PIS": pis_devido,
                "COFINS": cofins_devido,
                "ICMS": icms_devido,
                "ISS": iss_devido,
                "IPI": ipi_devido,
                "total": total,
                "economia_icms": resultado_icms["economia_tributaria"]  # Novo campo
            }

            return impostos

        except Exception as e:
            print(f"Erro no cálculo de impostos atuais: {e}")
            # Retornar valores padrão em caso de erro
            return {"PIS": 0, "COFINS": 0, "ICMS": 0, "ISS": 0, "IPI": 0, "total": 0}

    def calcular_icms_detalhado(self, dados):
        """Implementa o cálculo detalhado do ICMS considerando múltiplos incentivos fiscais."""
        try:
            # Obter dados básicos
            faturamento = dados.get("faturamento", 0)
            custos = dados.get("custos_tributaveis", 0)

            # Obter configurações específicas do ICMS
            aliquota_entrada = self.config.icms_config.get("aliquota_entrada", 0.19)
            aliquota_saida = self.config.icms_config.get("aliquota_saida", 0.19)
            incentivos_saida = self.config.icms_config.get("incentivos_saida", [])
            incentivos_entrada = self.config.icms_config.get("incentivos_entrada", [])

            # Criar memória de cálculo detalhada
            memoria_calculo = []
            memoria_calculo.append(f"Faturamento: R$ {formatar_br(faturamento)}")
            memoria_calculo.append(f"Custos tributáveis: R$ {formatar_br(custos)}")
            memoria_calculo.append(f"Alíquota média de entrada: {formatar_br(aliquota_entrada * 100)}%")
            memoria_calculo.append(f"Alíquota média de saída: {formatar_br(aliquota_saida * 100)}%")

            # Calcular débito e crédito normais (sem incentivo)
            debito_icms_normal = faturamento * aliquota_saida
            credito_normal = custos * aliquota_entrada

            memoria_calculo.append(
                f"Débito ICMS (sem incentivo): R$ {formatar_br(faturamento)} × {formatar_br(aliquota_saida * 100)}% = R$ {formatar_br(debito_icms_normal)}")
            memoria_calculo.append(
                f"Crédito normal: R$ {formatar_br(custos)} × {formatar_br(aliquota_entrada * 100)}% = R$ {formatar_br(credito_normal)}")

            # Se não houver incentivos configurados, retornar cálculo padrão
            if not incentivos_saida and not incentivos_entrada:
                icms_devido = debito_icms_normal - credito_normal
                memoria_calculo.append(f"Nenhum incentivo fiscal aplicado")
                memoria_calculo.append(
                    f"ICMS devido: R$ {formatar_br(debito_icms_normal)} - R$ {formatar_br(credito_normal)} = R$ {formatar_br(icms_devido)}")

                # Calcular economia tributária
                economia = 0
                percentual_economia = 0

                memoria_calculo.append(f"\nComparativo:")
                memoria_calculo.append(f"ICMS sem incentivo: R$ {formatar_br(icms_devido)}")
                memoria_calculo.append(f"ICMS com incentivo: R$ {formatar_br(icms_devido)}")
                memoria_calculo.append(
                    f"Economia tributária: R$ {formatar_br(economia)} ({formatar_br(percentual_economia)}%)")

                return {
                    "icms_devido": max(0, icms_devido),
                    "economia_tributaria": economia,
                    "percentual_economia": percentual_economia,
                    "memoria_calculo": memoria_calculo
                }

            # Processar incentivos de saída (débitos)
            debito_total = 0
            faturamento_nao_incentivado = faturamento

            memoria_calculo.append(f"\n== Processando incentivos para débitos de ICMS (saídas) ==")

            for idx, incentivo in enumerate(incentivos_saida, 1):
                tipo = incentivo.get("tipo", "Nenhum")
                percentual = incentivo.get("percentual", 0.0)
                percentual_operacoes = incentivo.get("percentual_operacoes", 1.0)
                descricao = incentivo.get("descricao", f"Incentivo {idx}")

                if tipo == "Nenhum" or percentual <= 0:
                    continue

                faturamento_incentivado = faturamento_nao_incentivado * percentual_operacoes
                faturamento_nao_incentivado -= faturamento_incentivado

                memoria_calculo.append(f"\nIncentivo de saída {idx}: {descricao}")
                memoria_calculo.append(f"Tipo: {tipo}")
                memoria_calculo.append(f"Percentual do incentivo: {formatar_br(percentual * 100)}%")
                memoria_calculo.append(f"Percentual de operações: {formatar_br(percentual_operacoes * 100)}%")
                memoria_calculo.append(f"Faturamento incentivado: R$ {formatar_br(faturamento_incentivado)}")

                if tipo == "Redução de Alíquota":
                    aliquota_reduzida = aliquota_saida * (1 - percentual)
                    debito_incentivado = faturamento_incentivado * aliquota_reduzida

                    memoria_calculo.append(
                        f"Alíquota reduzida: {formatar_br(aliquota_saida * 100)}% × (1 - {formatar_br(percentual * 100)}%) = {formatar_br(aliquota_reduzida * 100)}%")
                    memoria_calculo.append(
                        f"Débito com alíquota reduzida: R$ {formatar_br(faturamento_incentivado)} × {formatar_br(aliquota_reduzida * 100)}% = R$ {formatar_br(debito_incentivado)}")

                elif tipo == "Crédito Presumido/Outorgado":
                    debito_incentivado = faturamento_incentivado * aliquota_saida
                    credito_presumido = debito_incentivado * percentual
                    debito_incentivado -= credito_presumido

                    memoria_calculo.append(
                        f"Débito normal: R$ {formatar_br(faturamento_incentivado)} × {formatar_br(aliquota_saida * 100)}% = R$ {formatar_br(faturamento_incentivado * aliquota_saida)}")
                    memoria_calculo.append(
                        f"Crédito presumido/outorgado: R$ {formatar_br(faturamento_incentivado * aliquota_saida)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(credito_presumido)}")
                    memoria_calculo.append(
                        f"Débito após crédito presumido/outorgado: R$ {formatar_br(faturamento_incentivado * aliquota_saida)} - R$ {formatar_br(credito_presumido)} = R$ {formatar_br(debito_incentivado)}")

                elif tipo == "Redução de Base de Cálculo":
                    base_reduzida = faturamento_incentivado * (1 - percentual)
                    debito_incentivado = base_reduzida * aliquota_saida

                    memoria_calculo.append(
                        f"Base de cálculo reduzida: R$ {formatar_br(faturamento_incentivado)} × (1 - {formatar_br(percentual * 100)}%) = R$ {formatar_br(base_reduzida)}")
                    memoria_calculo.append(
                        f"Débito sobre base reduzida: R$ {formatar_br(base_reduzida)} × {formatar_br(aliquota_saida * 100)}% = R$ {formatar_br(debito_incentivado)}")

                elif tipo == "Diferimento":
                    valor_diferido = faturamento_incentivado * aliquota_saida * percentual
                    debito_incentivado = (faturamento_incentivado * aliquota_saida) - valor_diferido

                    memoria_calculo.append(
                        f"Valor total de débito: R$ {formatar_br(faturamento_incentivado * aliquota_saida)}")
                    memoria_calculo.append(
                        f"Valor diferido: R$ {formatar_br(faturamento_incentivado * aliquota_saida)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(valor_diferido)}")
                    memoria_calculo.append(
                        f"Débito após diferimento: R$ {formatar_br(faturamento_incentivado * aliquota_saida)} - R$ {formatar_br(valor_diferido)} = R$ {formatar_br(debito_incentivado)}")

                else:
                    debito_incentivado = faturamento_incentivado * aliquota_saida
                    memoria_calculo.append(f"Tipo de incentivo não implementado, utilizando cálculo padrão")
                    memoria_calculo.append(
                        f"Débito: R$ {formatar_br(faturamento_incentivado)} × {formatar_br(aliquota_saida * 100)}% = R$ {formatar_br(debito_incentivado)}")

                debito_total += debito_incentivado

            # Adicionar débito das operações não incentivadas
            if faturamento_nao_incentivado > 0:
                debito_nao_incentivado = faturamento_nao_incentivado * aliquota_saida
                debito_total += debito_nao_incentivado

                memoria_calculo.append(f"\nOperações não incentivadas:")
                memoria_calculo.append(f"Faturamento não incentivado: R$ {formatar_br(faturamento_nao_incentivado)}")
                memoria_calculo.append(
                    f"Débito sobre operações não incentivadas: R$ {formatar_br(faturamento_nao_incentivado)} × {formatar_br(aliquota_saida * 100)}% = R$ {formatar_br(debito_nao_incentivado)}")

            memoria_calculo.append(f"\nTotal de débitos após incentivos: R$ {formatar_br(debito_total)}")

            # Processar incentivos de entrada (créditos)
            credito_total = 0
            custos_nao_incentivados = custos

            memoria_calculo.append(f"\n== Processando incentivos para créditos de ICMS (entradas) ==")

            for idx, incentivo in enumerate(incentivos_entrada, 1):
                tipo = incentivo.get("tipo", "Nenhum")
                percentual = incentivo.get("percentual", 0.0)
                percentual_operacoes = incentivo.get("percentual_operacoes", 1.0)
                descricao = incentivo.get("descricao", f"Incentivo {idx}")

                if tipo == "Nenhum" or percentual <= 0:
                    continue

                custos_incentivados = custos_nao_incentivados * percentual_operacoes
                custos_nao_incentivados -= custos_incentivados

                memoria_calculo.append(f"\nIncentivo de entrada {idx}: {descricao}")
                memoria_calculo.append(f"Tipo: {tipo}")
                memoria_calculo.append(f"Percentual do incentivo: {formatar_br(percentual * 100)}%")
                memoria_calculo.append(f"Percentual de operações: {formatar_br(percentual_operacoes * 100)}%")
                memoria_calculo.append(f"Custos incentivados: R$ {formatar_br(custos_incentivados)}")

                if tipo == "Redução de Alíquota":
                    aliquota_reduzida = aliquota_entrada * (1 - percentual)
                    credito_incentivado = custos_incentivados * aliquota_reduzida

                    memoria_calculo.append(
                        f"Alíquota reduzida: {formatar_br(aliquota_entrada * 100)}% × (1 - {formatar_br(percentual * 100)}%) = {formatar_br(aliquota_reduzida * 100)}%")
                    memoria_calculo.append(
                        f"Crédito com alíquota reduzida: R$ {formatar_br(custos_incentivados)} × {formatar_br(aliquota_reduzida * 100)}% = R$ {formatar_br(credito_incentivado)}")

                elif tipo == "Crédito Presumido/Outorgado":
                    credito_base = custos_incentivados * aliquota_entrada
                    credito_adicional = credito_base * percentual
                    credito_incentivado = credito_base + credito_adicional

                    memoria_calculo.append(
                        f"Crédito base: R$ {formatar_br(custos_incentivados)} × {formatar_br(aliquota_entrada * 100)}% = R$ {formatar_br(credito_base)}")
                    memoria_calculo.append(
                        f"Crédito adicional: R$ {formatar_br(credito_base)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(credito_adicional)}")
                    memoria_calculo.append(
                        f"Crédito total: R$ {formatar_br(credito_base)} + R$ {formatar_br(credito_adicional)} = R$ {formatar_br(credito_incentivado)}")

                elif tipo == "Estorno de Crédito":
                    credito_base = custos_incentivados * aliquota_entrada
                    estorno = credito_base * percentual
                    credito_incentivado = credito_base - estorno

                    memoria_calculo.append(
                        f"Crédito base: R$ {formatar_br(custos_incentivados)} × {formatar_br(aliquota_entrada * 100)}% = R$ {formatar_br(credito_base)}")
                    memoria_calculo.append(
                        f"Estorno de crédito: R$ {formatar_br(credito_base)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(estorno)}")
                    memoria_calculo.append(
                        f"Crédito após estorno: R$ {formatar_br(credito_base)} - R$ {formatar_br(estorno)} = R$ {formatar_br(credito_incentivado)}")

                else:
                    credito_incentivado = custos_incentivados * aliquota_entrada
                    memoria_calculo.append(
                        f"Tipo de incentivo não implementado para entradas, utilizando cálculo padrão")
                    memoria_calculo.append(
                        f"Crédito: R$ {formatar_br(custos_incentivados)} × {formatar_br(aliquota_entrada * 100)}% = R$ {formatar_br(credito_incentivado)}")

                credito_total += credito_incentivado

                # Processar incentivos de apuração (aplicados sobre o saldo devedor)
                incentivos_apuracao = self.config.icms_config.get("incentivos_apuracao", [])
                icms_antes_incentivos_apuracao = max(0, debito_total - credito_total)

                memoria_calculo.append(f"\n== Processando incentivos de apuração do ICMS ==")
                memoria_calculo.append(
                    f"ICMS antes dos incentivos de apuração: R$ {formatar_br(icms_antes_incentivos_apuracao)}")

                # Se não há saldo devedor ou incentivos de apuração, não aplicar
                if icms_antes_incentivos_apuracao <= 0 or not incentivos_apuracao:
                    memoria_calculo.append(f"Não há saldo devedor ou incentivos de apuração configurados.")
                    icms_devido = icms_antes_incentivos_apuracao
                else:
                    reducao_total = 0

                    for idx, incentivo in enumerate(incentivos_apuracao, 1):
                        tipo = incentivo.get("tipo", "Nenhum")
                        percentual = incentivo.get("percentual", 0.0)
                        percentual_saldo = incentivo.get("percentual_operacoes", 1.0)  # Percentual do saldo
                        descricao = incentivo.get("descricao", f"Incentivo Apuração {idx}")

                        if tipo == "Nenhum" or percentual <= 0:
                            continue

                        saldo_afetado = icms_antes_incentivos_apuracao * percentual_saldo

                        memoria_calculo.append(f"\nIncentivo de apuração {idx}: {descricao}")
                        memoria_calculo.append(f"Tipo: {tipo}")
                        memoria_calculo.append(f"Percentual do incentivo: {formatar_br(percentual * 100)}%")
                        memoria_calculo.append(f"Percentual do saldo: {formatar_br(percentual_saldo * 100)}%")
                        memoria_calculo.append(f"Saldo afetado: R$ {formatar_br(saldo_afetado)}")

                        if tipo == "Crédito Presumido/Outorgado":
                            reducao = saldo_afetado * percentual
                            memoria_calculo.append(
                                f"Crédito outorgado: R$ {formatar_br(saldo_afetado)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(reducao)}")

                        elif tipo == "Redução do Saldo Devedor":
                            reducao = saldo_afetado * percentual
                            memoria_calculo.append(
                                f"Redução direta: R$ {formatar_br(saldo_afetado)} × {formatar_br(percentual * 100)}% = R$ {formatar_br(reducao)}")

                        else:
                            reducao = 0
                            memoria_calculo.append(f"Tipo de incentivo não implementado para apuração")

                        reducao_total += reducao

                    # Aplicar reduções
                    icms_devido = max(0, icms_antes_incentivos_apuracao - reducao_total)

                    memoria_calculo.append(f"\nTotal de reduções de apuração: R$ {formatar_br(reducao_total)}")
                    memoria_calculo.append(f"ICMS devido após incentivos de apuração: R$ {formatar_br(icms_devido)}")

            # Adicionar crédito das operações não incentivadas
            if custos_nao_incentivados > 0:
                credito_nao_incentivado = custos_nao_incentivados * aliquota_entrada
                credito_total += credito_nao_incentivado

                memoria_calculo.append(f"\nOperações de entrada não incentivadas:")
                memoria_calculo.append(f"Custos não incentivados: R$ {formatar_br(custos_nao_incentivados)}")
                memoria_calculo.append(
                    f"Crédito sobre operações não incentivadas: R$ {formatar_br(custos_nao_incentivados)} × {formatar_br(aliquota_entrada * 100)}% = R$ {formatar_br(credito_nao_incentivado)}")

            memoria_calculo.append(f"\nTotal de créditos após incentivos: R$ {formatar_br(credito_total)}")

            # Cálculo do ICMS devido
            icms_devido = max(0, debito_total - credito_total)

            memoria_calculo.append(f"\n== Cálculo final do ICMS ==")
            memoria_calculo.append(f"Débitos totais: R$ {formatar_br(debito_total)}")
            memoria_calculo.append(f"Créditos totais: R$ {formatar_br(credito_total)}")
            memoria_calculo.append(
                f"ICMS devido: R$ {formatar_br(debito_total)} - R$ {formatar_br(credito_total)} = R$ {formatar_br(icms_devido)}")

            # Calcular economia tributária
            icms_sem_incentivo = debito_icms_normal - credito_normal
            economia = icms_sem_incentivo - icms_devido
            percentual_economia = (economia / icms_sem_incentivo) * 100 if icms_sem_incentivo > 0 else 0

            memoria_calculo.append(f"\nComparativo:")
            memoria_calculo.append(f"ICMS sem incentivo: R$ {formatar_br(icms_sem_incentivo)}")
            memoria_calculo.append(f"ICMS com incentivo: R$ {formatar_br(icms_devido)}")
            memoria_calculo.append(
                f"Economia tributária: R$ {formatar_br(economia)} ({formatar_br(percentual_economia)}%)")

            return {
                "icms_devido": max(0, icms_devido),  # Garantir que não seja negativo
                "economia_tributaria": economia,
                "percentual_economia": percentual_economia,
                "memoria_calculo": memoria_calculo
            }

        except Exception as e:
            print(f"Erro no cálculo detalhado do ICMS: {e}")
            return {
                "icms_devido": 0,
                "economia_tributaria": 0,
                "percentual_economia": 0,
                "memoria_calculo": [f"Erro no cálculo: {str(e)}"]
            }

    def obter_memoria_calculo(self):
        """Retorna a memória de cálculo dos tributos."""
        return self.memoria_calculo


class CalculadoraIVADual:
    """Implementa os cálculos do IVA Dual conforme as regras da reforma tributária."""

    def __init__(self, configuracao):
        self.config = configuracao
        self.memoria_calculo = {}  # Para armazenar os passos do cálculo
        self.calculadora_atual = None

    def validar_dados(self, dados):
        """Valida os dados da empresa."""
        if dados["faturamento"] < 0:
            raise ValueError("Faturamento não pode ser negativo")
        if dados["custos_tributaveis"] > dados["faturamento"]:
            raise ValueError("Custos tributáveis não podem exceder o faturamento")
        if dados["regime"] == "simples" and dados["faturamento"] > self.config.limite_simples:
            raise ValueError(
                f"Empresas do Simples Nacional devem ter faturamento anual até R$ {formatar_br(self.config.limite_simples)}")
        return True

    def calcular_base_tributavel(self, dados, ano):
        """Calcula a base tributável considerando a fase de transição."""
        fator_transicao = self.config.fase_transicao.get(ano, 1.0)

        # Base de cálculo = Faturamento × (Fator de Transição)
        base = dados["faturamento"] * fator_transicao

        # Registrar memória de cálculo
        if "base_tributavel" not in self.memoria_calculo:
            self.memoria_calculo["base_tributavel"] = []

        self.memoria_calculo["base_tributavel"].append(f"Faturamento: R$ {formatar_br(dados['faturamento'])}")
        self.memoria_calculo["base_tributavel"].append(
            f"Fator de Transição ({ano}): {formatar_br(fator_transicao * 100)}%")
        self.memoria_calculo["base_tributavel"].append(
            f"Base de Cálculo: R$ {formatar_br(dados['faturamento'])} × {formatar_br(fator_transicao * 100)}% = R$ {formatar_br(base)}")

        # Ajuste para setores especiais
        if dados["setor"] in self.config.setores_especiais and dados["setor"] != "padrao":
            base_especial = dados["faturamento"] * (fator_transicao * 0.5)  # Redução adicional de 50% na base
            self.memoria_calculo["base_tributavel"].append(
                f"Setor especial ({dados['setor']}): Redução adicional de 50% na base")
            self.memoria_calculo["base_tributavel"].append(
                f"Base de Cálculo Ajustada: R$ {formatar_br(dados['faturamento'])} × ({formatar_br(fator_transicao * 100)}% × 0,5) = R$ {formatar_br(base_especial)}")
            return base_especial

        return base

    def calcular_creditos(self, dados, ano):
        """Calcula os créditos tributários disponíveis."""
        # Separar custos por origem
        custos_normais = dados.get("custos_tributaveis", 0)
        custos_simples = dados.get("custos_simples", 0)
        custos_rurais = dados.get("custos_rurais", 0)
        custos_importacoes = dados.get("custos_importacoes", 0)

        # Obter alíquotas efetivas
        aliquotas = self.config.obter_aliquotas_efetivas(dados["setor"], ano)

        # Registrar memória de cálculo
        if "creditos" not in self.memoria_calculo:
            self.memoria_calculo["creditos"] = []

        self.memoria_calculo["creditos"].append(f"Alíquotas efetivas para {dados['setor']} em {ano}:")
        self.memoria_calculo["creditos"].append(f"CBS: {formatar_br(aliquotas['CBS'] * 100)}%")
        self.memoria_calculo["creditos"].append(f"IBS: {formatar_br(aliquotas['IBS'] * 100)}%")
        self.memoria_calculo["creditos"].append(f"Total: {formatar_br(aliquotas['total'] * 100)}%")

        # Calcular créditos por tipo de origem
        creditos = 0

        # Créditos de fornecedores do regime normal
        if custos_normais > 0:
            credito_normal = custos_normais * (aliquotas["CBS"] + aliquotas["IBS"])
            self.memoria_calculo["creditos"].append(f"\nCréditos de Fornecedores do Regime Normal:")
            self.memoria_calculo["creditos"].append(f"Custos: R$ {formatar_br(custos_normais)}")
            self.memoria_calculo["creditos"].append(
                f"Crédito: R$ {formatar_br(custos_normais)} × ({formatar_br(aliquotas['CBS'] * 100)}% + {formatar_br(aliquotas['IBS'] * 100)}%) = R$ {formatar_br(credito_normal)}")
            creditos += credito_normal

        # Créditos do Simples Nacional (limitado a 20%)
        if custos_simples > 0:
            base_credito_simples = custos_simples * self.config.regras_credito["simples"]
            credito_simples = base_credito_simples * (aliquotas["CBS"] + aliquotas["IBS"])

            self.memoria_calculo["creditos"].append(f"\nCréditos de Fornecedores do Simples Nacional:")
            self.memoria_calculo["creditos"].append(f"Custos: R$ {formatar_br(custos_simples)}")
            self.memoria_calculo["creditos"].append(
                f"Limite de aproveitamento: {formatar_br(self.config.regras_credito['simples'] * 100)}%")
            self.memoria_calculo["creditos"].append(
                f"Base para crédito: R$ {formatar_br(custos_simples)} × {formatar_br(self.config.regras_credito['simples'] * 100)}% = R$ {formatar_br(base_credito_simples)}")
            self.memoria_calculo["creditos"].append(
                f"Crédito: R$ {formatar_br(base_credito_simples)} × ({formatar_br(aliquotas['CBS'] * 100)}% + {formatar_br(aliquotas['IBS'] * 100)}%) = R$ {formatar_br(credito_simples)}")

            # Limitação adicional (40% do imposto devido)
            imposto_devido = dados.get("imposto_devido", credito_simples * 2.5)
            limite_imposto = imposto_devido * 0.40
            credito_final = min(credito_simples, limite_imposto)

            self.memoria_calculo["creditos"].append(
                f"Limite adicional (40% do imposto devido): R$ {formatar_br(imposto_devido)} × 40% = R$ {formatar_br(limite_imposto)}")
            self.memoria_calculo["creditos"].append(f"Crédito final (menor valor): R$ {formatar_br(credito_final)}")

            creditos += credito_final

        # Créditos de produtores rurais (60% sobre CBS)
        if custos_rurais > 0:
            credito_rural = custos_rurais * (
                    aliquotas["IBS"] + (aliquotas["CBS"] * self.config.regras_credito["rural"]))

            self.memoria_calculo["creditos"].append(f"\nCréditos de Produtores Rurais:")
            self.memoria_calculo["creditos"].append(f"Custos: R$ {formatar_br(custos_rurais)}")
            self.memoria_calculo["creditos"].append(
                f"Aproveitamento CBS: {formatar_br(self.config.regras_credito['rural'] * 100)}%")
            self.memoria_calculo["creditos"].append(
                f"Crédito: R$ {formatar_br(custos_rurais)} × ({formatar_br(aliquotas['IBS'] * 100)}% + ({formatar_br(aliquotas['CBS'] * 100)}% × {formatar_br(self.config.regras_credito['rural'] * 100)}%)) = R$ {formatar_br(credito_rural)}")

            creditos += credito_rural

        # Créditos de importações
        if custos_importacoes > 0:
            credito_importacao = custos_importacoes * (
                    aliquotas["IBS"] * self.config.regras_credito["importacoes"]["IBS"] +
                    aliquotas["CBS"] * self.config.regras_credito["importacoes"]["CBS"]
            )

            self.memoria_calculo["creditos"].append(f"\nCréditos de Importações:")
            self.memoria_calculo["creditos"].append(f"Custos: R$ {formatar_br(custos_importacoes)}")
            self.memoria_calculo["creditos"].append(
                f"Aproveitamento IBS: {formatar_br(self.config.regras_credito['importacoes']['IBS'] * 100)}%")
            self.memoria_calculo["creditos"].append(
                f"Aproveitamento CBS: {formatar_br(self.config.regras_credito['importacoes']['CBS'] * 100)}%")
            self.memoria_calculo["creditos"].append(
                f"Crédito: R$ {formatar_br(custos_importacoes)} × ({formatar_br(aliquotas['IBS'] * 100)}% × {formatar_br(self.config.regras_credito['importacoes']['IBS'] * 100)}% + {formatar_br(aliquotas['CBS'] * 100)}% × {formatar_br(self.config.regras_credito['importacoes']['CBS'] * 100)}%) = R$ {formatar_br(credito_importacao)}")

            creditos += credito_importacao

        # Adicionar créditos anteriores
        creditos_anteriores = dados.get("creditos_anteriores", 0)
        if creditos_anteriores > 0:
            self.memoria_calculo["creditos"].append(f"\nCréditos Anteriores:")
            self.memoria_calculo["creditos"].append(f"Valor: R$ {formatar_br(creditos_anteriores)}")
            creditos += creditos_anteriores

        # Total de créditos
        self.memoria_calculo["creditos"].append(f"\nTotal de Créditos: R$ {formatar_br(creditos)}")

        return creditos

    def calcular_imposto_devido(self, dados, ano):
        """Calcula o imposto devido aplicando o IVA Dual, considerando a transição."""
        # Limpar memória de cálculo anterior
        self.memoria_calculo = {
            "validacao": [],
            "base_tributavel": [],
            "aliquotas": [],
            "cbs": [],
            "ibs": [],
            "creditos": [],
            "imposto_devido": [],
            "impostos_atuais": [],
            "creditos_cruzados": [],
            "total_devido": []
        }

        # Validar dados
        try:
            self.validar_dados(dados)
            self.memoria_calculo["validacao"].append("Dados validados com sucesso.")
        except ValueError as e:
            self.memoria_calculo["validacao"].append(f"Erro de validação: {str(e)}")
            raise

        # Calcular base tributável
        base = self.calcular_base_tributavel(dados, ano)

        # Obter alíquotas efetivas para o setor
        aliquotas = self.config.obter_aliquotas_efetivas(dados["setor"], ano)

        self.memoria_calculo["aliquotas"].append(f"Alíquotas para o setor {dados['setor']} em {ano}:")
        self.memoria_calculo["aliquotas"].append(f"CBS: {formatar_br(aliquotas['CBS'] * 100)}%")
        self.memoria_calculo["aliquotas"].append(f"IBS: {formatar_br(aliquotas['IBS'] * 100)}%")
        self.memoria_calculo["aliquotas"].append(f"Total: {formatar_br(aliquotas['total'] * 100)}%")

        # Calcular CBS e IBS
        cbs = base * aliquotas["CBS"]
        ibs = base * aliquotas["IBS"]
        imposto_bruto = cbs + ibs

        self.memoria_calculo["cbs"].append(f"Cálculo da CBS:")
        self.memoria_calculo["cbs"].append(f"Base tributável: R$ {formatar_br(base)}")
        self.memoria_calculo["cbs"].append(f"Alíquota CBS: {formatar_br(aliquotas['CBS'] * 100)}%")
        self.memoria_calculo["cbs"].append(
            f"CBS = R$ {formatar_br(base)} × {formatar_br(aliquotas['CBS'] * 100)}% = R$ {formatar_br(cbs)}")

        self.memoria_calculo["ibs"].append(f"Cálculo do IBS:")
        self.memoria_calculo["ibs"].append(f"Base tributável: R$ {formatar_br(base)}")
        self.memoria_calculo["ibs"].append(f"Alíquota IBS: {formatar_br(aliquotas['IBS'] * 100)}%")
        self.memoria_calculo["ibs"].append(
            f"IBS = R$ {formatar_br(base)} × {formatar_br(aliquotas['IBS'] * 100)}% = R$ {formatar_br(ibs)}")

        self.memoria_calculo["imposto_devido"].append(f"Imposto Bruto (CBS + IBS):")
        self.memoria_calculo["imposto_devido"].append(
            f"Imposto Bruto = R$ {formatar_br(cbs)} + R$ {formatar_br(ibs)} = R$ {formatar_br(imposto_bruto)}")

        # Abordagem em duas etapas para o cálculo de créditos
        # 1. Primeiro calculamos os créditos que não dependem do imposto devido
        dados_iniciais = dados.copy()
        dados_iniciais["imposto_devido"] = imposto_bruto  # Estimativa inicial
        creditos = self.calcular_creditos(dados_iniciais, ano)

        # 2. Calcular o imposto devido final
        imposto_devido = max(0, imposto_bruto - creditos)

        self.memoria_calculo["imposto_devido"].append(f"Cálculo do Imposto Devido:")
        self.memoria_calculo["imposto_devido"].append(f"Imposto Devido = Imposto Bruto - Créditos")
        self.memoria_calculo["imposto_devido"].append(
            f"Imposto Devido = R$ {formatar_br(imposto_bruto)} - R$ {formatar_br(creditos)} = R$ {formatar_br(imposto_devido)}")

        # Calcular impostos do sistema atual
        if not self.calculadora_atual:
            self.calculadora_atual = CalculadoraTributosAtuais(self.config)

        impostos_atuais = self.calculadora_atual.calcular_todos_impostos(dados, ano)

        # Registrar memória de cálculo dos impostos atuais
        self.memoria_calculo["impostos_atuais"] = self.calculadora_atual.memoria_calculo

        # Aplicar créditos cruzados se aplicável
        if ano in self.config.creditos_cruzados:
            self.memoria_calculo["creditos_cruzados"].append(f"Aplicação de Créditos Cruzados (ano {ano}):")

            percentual_ibs_para_icms = self.config.creditos_cruzados[ano].get("IBS_para_ICMS", 0)
            self.memoria_calculo["creditos_cruzados"].append(
                f"Percentual do IBS aproveitável para ICMS: {formatar_br(percentual_ibs_para_icms * 100)}%")

            credito_ibs_para_icms = min(
                ibs * percentual_ibs_para_icms,
                impostos_atuais.get("ICMS", 0)
            )

            self.memoria_calculo["creditos_cruzados"].append(f"Limite de crédito: min(IBS × Percentual, ICMS)")
            self.memoria_calculo["creditos_cruzados"].append(
                f"Limite de crédito: min(R$ {formatar_br(ibs)} × {formatar_br(percentual_ibs_para_icms * 100)}%, R$ {formatar_br(impostos_atuais.get('ICMS', 0))})")
            self.memoria_calculo["creditos_cruzados"].append(
                f"Limite de crédito: min(R$ {formatar_br(ibs * percentual_ibs_para_icms)}, R$ {formatar_br(impostos_atuais.get('ICMS', 0))})")
            self.memoria_calculo["creditos_cruzados"].append(
                f"Crédito IBS para ICMS: R$ {formatar_br(credito_ibs_para_icms)}")

            # Atualizar ICMS devido após crédito cruzado
            icms_original = impostos_atuais.get("ICMS", 0)
            icms_final = icms_original - credito_ibs_para_icms

            self.memoria_calculo["creditos_cruzados"].append(f"ICMS original: R$ {formatar_br(icms_original)}")
            self.memoria_calculo["creditos_cruzados"].append(
                f"ICMS final após crédito cruzado: R$ {formatar_br(icms_original)} - R$ {formatar_br(credito_ibs_para_icms)} = R$ {formatar_br(icms_final)}")

            impostos_atuais["ICMS"] = icms_final
            impostos_atuais["total"] = sum(value for key, value in impostos_atuais.items() if key != "total")

            self.memoria_calculo["creditos_cruzados"].append(
                f"Total de impostos atuais após crédito cruzado: R$ {formatar_br(impostos_atuais['total'])}")

        # Cálculo do total devido
        total_devido = imposto_devido + impostos_atuais.get("total", 0)

        self.memoria_calculo["total_devido"].append(f"Cálculo do Total Devido:")
        self.memoria_calculo["total_devido"].append(f"Total Devido = Imposto Devido (IVA Dual) + Total Impostos Atuais")
        self.memoria_calculo["total_devido"].append(
            f"Total Devido = R$ {formatar_br(imposto_devido)} + R$ {formatar_br(impostos_atuais.get('total', 0))} = R$ {formatar_br(total_devido)}")

        # Alíquota efetiva
        if dados["faturamento"] > 0:
            aliquota_efetiva = total_devido / dados["faturamento"]
            self.memoria_calculo["total_devido"].append(
                f"Alíquota Efetiva: R$ {formatar_br(total_devido)} ÷ R$ {formatar_br(dados['faturamento'])} = {formatar_br(aliquota_efetiva * 100)}%")
        else:
            aliquota_efetiva = 0
            self.memoria_calculo["total_devido"].append(f"Alíquota Efetiva: 0% (faturamento zero)")

        # Resultado detalhado
        resultado = {
            "ano": ano,
            "base_tributavel": base,
            "cbs": cbs,
            "ibs": ibs,
            "imposto_bruto": imposto_bruto,
            "creditos": creditos,
            "imposto_devido": imposto_devido,
            "impostos_atuais": impostos_atuais,
            "total_devido": total_devido,
            "aliquota_efetiva": aliquota_efetiva,
            "aliquotas_utilizadas": aliquotas
        }

        return resultado

    def obter_memoria_calculo(self):
        """Retorna a memória de cálculo dos tributos."""
        return self.memoria_calculo

    def calcular_comparativo(self, dados, anos=None):
        """Compara o imposto devido em diferentes anos da transição."""
        if anos is None:
            anos = list(self.config.fase_transicao.keys())

        resultados = {}
        for ano in anos:
            resultados[ano] = self.calcular_imposto_devido(dados, ano)

        return resultados

    def calcular_aliquotas_equivalentes(self, dados, carga_atual, ano):
        """Calcula as alíquotas de CBS e IBS que resultariam em carga tributária equivalente à atual."""
        # Fator de transição para o ano
        fator_transicao = self.config.fase_transicao.get(ano, 1.0)

        # Base tributável
        base = self.calcular_base_tributavel(dados, ano)

        # Valor atual de impostos
        valor_atual = dados["faturamento"] * (carga_atual / 100)

        # Considerando a proporção atual entre CBS e IBS (geralmente 1:2)
        proporcao_cbs = 1 / 3  # CBS representa aproximadamente 1/3 do IVA Dual

        # Adaptação para o setor específico
        setor_config = self.config.setores_especiais.get(dados["setor"], self.config.setores_especiais["padrao"])
        reducao_cbs = setor_config["reducao_CBS"]

        # Ajuste na proporção considerando reduções setoriais
        if reducao_cbs > 0:
            # Se há redução de CBS, a proporção do IBS aumenta
            proporcao_cbs = proporcao_cbs * (1 - reducao_cbs)

        # Créditos estimados (simplificação)
        creditos_estimados = 0
        if dados["custos_tributaveis"] > 0:
            # Estimativa: créditos proporcionais aos custos tributáveis
            creditos_estimados = (dados["custos_tributaveis"] / dados["faturamento"]) * valor_atual

        # Imposto bruto necessário para atingir o valor atual após créditos
        imposto_bruto_necessario = valor_atual + creditos_estimados

        # Alíquotas equivalentes
        if base > 0:
            aliquota_total = imposto_bruto_necessario / base
            aliquota_cbs = aliquota_total * proporcao_cbs
            aliquota_ibs = aliquota_total * (1 - proporcao_cbs)
        else:
            aliquota_cbs = 0
            aliquota_ibs = 0

        return {
            "cbs_equivalente": aliquota_cbs,
            "ibs_equivalente": aliquota_ibs,
            "total_equivalente": aliquota_cbs + aliquota_ibs,
            "valor_atual": valor_atual,
            "base_calculo": base
        }