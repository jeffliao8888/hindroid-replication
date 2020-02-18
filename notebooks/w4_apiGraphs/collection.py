from glob import glob


def get_smali(smali_path):
    '''
    get all filenames in smali_path with .smali
    input: directory
    '''
    return glob('%s/**/*.smali' % smali_path, recursive=True)
