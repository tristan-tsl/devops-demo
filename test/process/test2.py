from common.common_service import MyServiceException


def is_cur_user_process(cur_step):
    pass


def do_next(process_steps, level=1):
    process_steps = process_steps.strip()
    if not process_steps or len(process_steps) < 1:
        raise MyServiceException("流程(%s)不能为空" % process_steps)

    # 计算cur_step、next_step、next_steps
    first_step_sep_index = process_steps.find(">")
    next_steps = ""
    next_step = ""
    # 剩余节点
    if first_step_sep_index <= 0:
        cur_step = process_steps
    else:
        cur_step = process_steps[0:first_step_sep_index]
        if level != 0:
            next_steps = process_steps[first_step_sep_index + 1:]
            try:
                cur_step_temp, next_step_temp, next_steps_temp = do_next(next_steps, level=0)
                next_step = cur_step_temp
            except MyServiceException as e:
                print(e)

    return cur_step, next_step, next_steps


if __name__ == '__main__':
    process_temp = "test"
    cur_step_temp, next_step_temp, next_steps_temp = do_next(process_temp)
    print(cur_step_temp)
