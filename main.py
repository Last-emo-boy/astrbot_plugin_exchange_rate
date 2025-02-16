from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, command, llm_tool
from astrbot.api.star import Context, Star, register
import aiohttp
from mapping import currency_mapping

@register("exchange_rate", "w33d", "汇率查询机器人插件", "1.0.0", "https://github.com/Last-emo-boy/astrbot_plugin_exchange_rate")
class ExchangeRatePlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.apikey = config.get("apikey", "")
        if not self.apikey:
            print("警告：API Key 未配置，请在配置文件中设置apikey。")

    @command("汇率查询")
    async def query_exchange_rate(self, event: AstrMessageEvent, base: str, target: str = None):
        """
        查询汇率指令。
        
        参数:
            base(string): 基础货币，可以是中文（例如“美元”）或ISO代码（例如“USD”）。
            target(string, 可选): 目标货币，可以是中文（例如“欧元”）或ISO代码（例如“EUR”）。不填则返回所有汇率。
        """
        # 将输入的基础货币转换为 ISO 代码（支持中文映射）
        base_code = currency_mapping.get(base, base.upper())
        if target:
            target_code = currency_mapping.get(target, target.upper())
        else:
            target_code = None

        url = f"https://v6.exchangerate-api.com/v6/{self.apikey}/latest/{base_code}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        if data.get("result") != "success":
            error_type = data.get("error-type", "未知错误")
            yield event.plain_result(f"查询失败: {error_type}")
            return

        rates = data.get("conversion_rates", {})
        if target_code:
            rate = rates.get(target_code)
            if rate is None:
                yield event.plain_result(f"目标货币 {target} 不支持查询。")
            else:
                yield event.plain_result(f"{base_code} 到 {target_code} 的汇率是: {rate}")
        else:
            lines = [f"{base_code} 汇率："]
            for code, rate in rates.items():
                lines.append(f"{code}: {rate}")
            yield event.plain_result("\n".join(lines))

    @llm_tool(name="get_exchange_rate")
    async def get_exchange_rate(self, event: AstrMessageEvent, base: str, target: str) -> MessageEventResult:
        """
        查询汇率信息的 LLM 工具。
        
        Args:
            base(string): 基础货币，可以使用中文（如“美元”）或 ISO 代码（如“USD”）。
            target(string): 目标货币，可以使用中文（如“欧元”）或 ISO 代码（如“EUR”）。
        """
        base_code = currency_mapping.get(base, base.upper())
        target_code = currency_mapping.get(target, target.upper())

        url = f"https://v6.exchangerate-api.com/v6/{self.apikey}/latest/{base_code}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        if data.get("result") != "success":
            error_type = data.get("error-type", "未知错误")
            yield event.plain_result(f"查询失败: {error_type}")
            return

        rates = data.get("conversion_rates", {})
        rate = rates.get(target_code)
        if rate is None:
            yield event.plain_result(f"目标货币 {target} 不支持查询。")
        else:
            yield event.plain_result(f"{base_code} 到 {target_code} 的汇率是: {rate}")
