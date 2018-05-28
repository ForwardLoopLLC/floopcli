from test.lambda_function import Lambda

if __name__ == '__main__':
    Lambda().\
    make_zip_archive(). \
    create_or_update_function(). \
    publish_function_version(). \
    create_alias()
