ignore_methods = ["OPTIONS", "HEAD"]
ignore_rules_key = ["static", "static_path", "index", "url_map"]


class MyFlask(object):
    def __init__(self, app):
        self.app = app

    def get_endpoint_list(self):
        res_data = []
        rules = self.app.url_map._rules_by_endpoint
        for rule_item_key in rules:
            if rule_item_key in ignore_rules_key:
                continue
            rule_item = rules[rule_item_key]
            rule_item_data = rule_item[0]
            rule_item_data_rule = rule_item_data.rule
            rule_item_data_methods = rule_item_data.methods
            for method_item in rule_item_data_methods:
                if method_item in ignore_methods:
                    continue
                rule_item_data_rule += ":%s" % method_item.lower()
                res_data.append(rule_item_data_rule)
        return res_data
