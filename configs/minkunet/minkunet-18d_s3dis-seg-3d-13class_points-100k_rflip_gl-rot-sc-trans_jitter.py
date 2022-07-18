_base_ = [
    '../_base_/models/minkunet.py',
    '../_base_/default_runtime.py',
]
num_points = 100000
file_client_args = dict(backend='disk')
class_names = ('ceiling', 'floor', 'wall', 'beam', 'column', 'window', 'door',
               'table', 'chair', 'sofa', 'bookcase', 'board', 'clutter')

train_pipeline = [
    dict(
        type='LoadPointsFromFile',
        file_client_args=file_client_args,
        coord_type='DEPTH',
        shift_height=False,
        use_color=True,
        load_dim=6,
        use_dim=[0, 1, 2, 3, 4, 5],
    ),
    dict(type='LoadAnnotations3D',
        file_client_args=file_client_args,
        with_bbox_3d=False,
        with_label_3d=False,
        with_mask_3d=False,
        with_seg_3d=True,
    ),
    dict(
        type='PointSegClassMapping',
        valid_cat_ids=tuple(range(len(class_names))),
        max_cat_id=13),
    dict(
        type='IndoorPatchPointSample',
        num_points=num_points,
        block_size=1.0,
        ignore_index=len(class_names),
        use_normalized_coord=True,
        enlarge_size=0.2,
        min_unique_num=None),
    dict(
        type='YOLOXHSVPointsRandomAug',
        hue_delta=2,
        saturation_delta=15,
        value_delta=15,
    ),
    dict(
        type='NormalizePointsColor',
        color_mean=None,
    ),
    dict(
        type='GlobalRotScaleTrans',
        rot_range=[-0.087266, 0.087266],
        scale_ratio_range=[.9, 1.1],
        translation_std=[.1, .1, .1],
        shift_height=False,
    ),
    dict(
        type='RandomFlip3D',
        sync_2d=False,
        flip_ratio_bev_horizontal=0.5,
        flip_ratio_bev_vertical=0.5,
    ),
    dict(type='DefaultFormatBundle3D', class_names=class_names),
    dict(type='Collect3D', keys=['points', 'pts_semantic_mask']),
]

# construct a pipeline for data and gt loading in show function
# please keep its loading function consistent with test_pipeline (e.g. client)
# we need to load gt seg_mask!
eval_pipeline = [
    dict(
        type='LoadPointsFromFile',
        file_client_args=file_client_args,
        coord_type='DEPTH',
        shift_height=False,
        use_color=True,
        load_dim=6,
        use_dim=[0, 1, 2, 3, 4, 5],
    ),
    dict(
        type='LoadAnnotations3D',
        file_client_args=file_client_args,
        with_bbox_3d=False,
        with_label_3d=False,
        with_mask_3d=False,
        with_seg_3d=True,
    ),
    dict(
        type='PointSegClassMapping',
        valid_cat_ids=tuple(range(len(class_names))),
        max_cat_id=13,
    ),
    dict(
        type='NormalizePointsColor',
        color_mean=None,
    ),
    dict(
        type='DefaultFormatBundle3D',
        with_label=False,
        class_names=class_names,
    ),
    dict(type='Collect3D', keys=['points', 'pts_semantic_mask'])
]

test_pipeline = [
    dict(
        type='LoadPointsFromFile',
        file_client_args=file_client_args,
        coord_type='DEPTH',
        shift_height=False,
        use_color=True,
        load_dim=6,
        use_dim=[0, 1, 2, 3, 4, 5]),
    dict(type='NormalizePointsColor', color_mean=None),
    dict(
        # a wrapper in order to successfully call test function
        # actually we don't perform test-time-aug
        type='MultiScaleFlipAug3D',
        img_scale=(1333, 800),
        pts_scale_ratio=1,
        flip=False,
        transforms=[
            dict(
                type='GlobalRotScaleTrans',
                rot_range=[0, 0],
                scale_ratio_range=[1., 1.],
                translation_std=[0, 0, 0]),
            dict(
                type='RandomFlip3D',
                sync_2d=False,
                flip_ratio_bev_horizontal=0.5,
                flip_ratio_bev_vertical=0.5),
            dict(
                type='DefaultFormatBundle3D',
                class_names=class_names,
                with_label=False),
            dict(type='Collect3D', keys=['points'])
        ])
]

evaluation = dict(pipeline=eval_pipeline, interval=1)
custom_hooks = [dict(type='EmptyCacheHook', after_iter=True)]
# runtime settings
checkpoint_config = dict(interval=1, max_keep_ckpts=1)
optimizer = dict(type='AdamW', lr=0.001, weight_decay=0.01)
# max_norm=10 is better for SECOND
optimizer_config = dict(grad_clip=dict(max_norm=35, norm_type=2))
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=1.0 / 1000,
    step=[8, 11])
momentum_config = None
# runtime settings
runner = dict(type='EpochBasedRunner', max_epochs=12)

# model settings
model = dict(
    type='SparseEncoderDecoder3D',
    voxel_size=0.05,
    backbone=dict(
        type='MinkUNetBase',
        depth=18,
        in_channels=3,
        D=3,
    ),
    decode_head=dict(
        type='MinkUNetHead',
        num_classes=13,
        ignore_index=13,
        loss_decode=dict(
            type='FocalLoss',
            use_sigmoid=True,
            reduction='sum',
            gamma=2.0,
            alpha=0.25,
            loss_weight=1.0,
        )))

dataset_type = 'S3DISSegDataset'
data_root = './data/s3dis/'
train_area = [1, 2, 3, 4, 6]
test_area = 5

data = dict(
    samples_per_gpu=32,
    workers_per_gpu=8,
    # train on area 1, 2, 3, 4, 6
    # test on area 5
    train=dict(
        type=dataset_type,
        data_root=data_root,
        ann_files=[
            data_root + f's3dis_infos_Area_{i}.pkl' for i in train_area
        ],
        pipeline=train_pipeline,
        classes=class_names,
        test_mode=False,
        ignore_index=len(class_names),
        scene_idxs=[
            data_root + f'seg_info/Area_{i}_resampled_scene_idxs.npy'
            for i in train_area
        ],
        file_client_args=file_client_args),
    val=dict(
        type=dataset_type,
        data_root=data_root,
        ann_files=data_root + f's3dis_infos_Area_{test_area}.pkl',
        pipeline=test_pipeline,
        classes=class_names,
        test_mode=True,
        ignore_index=len(class_names),
        scene_idxs=data_root +
        f'seg_info/Area_{test_area}_resampled_scene_idxs.npy',
        file_client_args=file_client_args),
    test=dict(
        type=dataset_type,
        data_root=data_root,
        ann_files=data_root + f's3dis_infos_Area_{test_area}.pkl',
        pipeline=test_pipeline,
        classes=class_names,
        test_mode=True,
        ignore_index=len(class_names),
        file_client_args=file_client_args))
