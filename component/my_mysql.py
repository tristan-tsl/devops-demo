import sqlparse


class AnalysisSQl(object):
    @staticmethod
    def get_table_name(sql):
        parse_results = sqlparse.parse(sql)
        parse_result = parse_results[0]
        tokens = parse_result.tokens
        for token in tokens:
            try:
                if type(token) == sqlparse.sql.Identifier:
                    return token.value
                inner_tokens = token.tokens
                for inner_token in inner_tokens:
                    if type(inner_token) == sqlparse.sql.Identifier:
                        return inner_token.value
            except:
                pass
