from common.common_service import MyServiceException

test_str = "EEEEEEEEEEEEEEEE > 111111111111 > 222222222222 > mZniSh9gJxOkdZzqn7IumLQiEiE > mZniSh9gJxOkdZzqn7IumLQiEiE > mZniSh9gJxOkdZzqn7IumLQiEiE"




if __name__ == '__main__':
    do_next_flag, next_step, next_steps = do_next(test_str)
    print(do_next_flag)
    print(next_step)
    print(next_steps)
