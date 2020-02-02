from glob import glob


def get_smali(smali_path, **kwargs):
    return glob('%s/**/*.smali' % smali_path, recursive=True)
