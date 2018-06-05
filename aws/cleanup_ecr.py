#!/usr/bin/env python

import re
import boto3


def get_nums(my_str):
    return list(map(int, re.findall(r'\d+', my_str)))


def batch(iterable, batch_number=1):
    length_iterable = len(iterable)
    for ndx in range(0, length_iterable, batch_number):
        yield iterable[ndx:min(ndx + batch_number, length_iterable)]


def delete_untagged(img_untagged_lst, boto_ecr, ecr_repo):
    print("Deleting untagged images for {}".format(ecr_repo))
    if len(img_untagged_lst) > 100:
        print("Untagged imgs : {}".format(len(img_untagged_lst)))
        print("Chunks to delete : {}".format(len(img_untagged_lst) / 100))

        for chunk in batch(img_untagged_lst, 99):
            boto_ecr.batch_delete_image(repositoryName=ecr_repo, imageIds=chunk)
    else:
        print("There are {} images to delete".format(len(img_untagged_lst)))
        boto_ecr.batch_delete_image(repositoryName=ecr_repo, imageIds=img_untagged_lst)
    print("Deleted all untagged images")


def delete_improperly_tagged(regex_verif, img_tagged_lst, boto_ecr, ecr_repo):
    tagged_goodbye_list = []
    pattern = re.compile(regex_verif)
    for t_img in img_tagged_lst:
        if t_img['imageTag'] != 'latest':
            if not pattern.match(t_img['imageTag']):
                tagged_goodbye_list.append(t_img)
                print(t_img)

    if len(tagged_goodbye_list) > 0:
        print("Delete {}".format(tagged_goodbye_list))
        boto_ecr.batch_delete_image(repositoryName=ecr_repo, imageIds=tagged_goodbye_list)
    else:
        print("Repo {} is clean.".format(ecr_repo))


def main():
    valid_tag_regex = '^(.*\-.*\-b?r?[0-9]+)$'

    client = boto3.client('ecr')
    list_repo = client.describe_repositories()
    list_image_paginator = client.get_paginator('list_images')

    for repo in list_repo['repositories']:
        list_imgs_iterator = list_image_paginator.paginate(repositoryName=repo['repositoryName'])
        tagged_images = []
        untagged_images = []

        for list_response in list_imgs_iterator:
            images = list_response.get('imageIds')
            if images:
                for image in images:
                    if 'imageTag' in image.keys():
                        tagged_images.append(image)
                    else:
                        untagged_images.append(image)

        if untagged_images:
            delete_untagged(untagged_images, client, repo['repositoryName'])

        if tagged_images:
            print("Processing tagged images of repo {}".format(repo['repositoryName']))
            delete_improperly_tagged(valid_tag_regex, tagged_images, client, repo['repositoryName'])


if __name__ == "__main__":
    main()
