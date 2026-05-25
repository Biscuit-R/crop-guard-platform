import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from app.utils.paths import Paths

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    APP_NAME: str = "Crop Guard Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8081

    STATIC_DIR: str = str(Paths.static())
    UPLOAD_DIR: str = str(Paths.uploads())
    RESULT_DIR: str = str(Paths.results())
    VIDEO_DIR: str = str(Paths.videos())
    RESULT_VIDEO_DIR: str = str(Paths.result_videos())
    VIDEO_MAX_SIZE: int = 200 * 1024 * 1024  # 200MB

    YOLO_MODEL_PATH: str = str(Paths.yolo_model())
    MODEL_DIR: str = str(Paths.models_dir())
    CONFIDENCE_THRESHOLD: float = 0.5
    IOU_THRESHOLD: float = 0.45

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_USER: str = "crop_user"
    DB_PASSWORD: str = "crop_password"
    DB_NAME: str = "crop_guard_db"

    # JWT配置
    JWT_SECRET_KEY: str = "crop-guard-secret-key-change-in-production"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时

    CORS_ORIGINS: list = ["http://localhost:5174", "http://localhost:3000"]

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9002"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "crop-guard-bucket"
    MINIO_SECURE: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# 安全凭据默认值列表（用于启动时检测）
_INSECURE_DEFAULTS = {
    "JWT_SECRET_KEY": "crop-guard-secret-key-change-in-production",
    "DB_PASSWORD": "crop_password",
    "MINIO_ACCESS_KEY": "minioadmin",
    "MINIO_SECRET_KEY": "minioadmin",
}


def _check_insecure_defaults(settings: Settings):
    """检测不安全的默认凭据并发出警告"""
    for field, default_val in _INSECURE_DEFAULTS.items():
        if getattr(settings, field) == default_val:
            logger.warning(
                "[安全警告] %s 使用了默认值，生产环境请通过 .env 文件覆盖", field
            )


settings = Settings()
_check_insecure_defaults(settings)


# 模型注册表：将文件名映射到显示名称
MODEL_REGISTRY = {
    "best.pt": {
        "display_name": "病虫害检测-v1.0.0-轻量版",
        "description": "基于67类平衡数据集训练，轻量级检测模型",
    },
}

# 英文类别名 → 中文学名映射
CHINESE_CLASS_NAMES = {
    # 水稻害虫
    "rice_leaf_roller": "稻纵卷叶螟",
    "rice_leaf_caterpillar": "稻螟蛉",
    "paddy_stem_maggot": "稻秆蝇",
    "asiatic_rice_borer": "二化螟",
    "yellow_rice_borer": "稻褐边螟",
    "rice_gall_midge": "稻瘿蚊",
    "Rice_Stemfly": "稻潜叶蝇",
    "brown_plant_hopper": "褐飞虱",
    "white_backed_plant_hopper": "白背飞虱",
    "small_brown_plant_hopper": "灰飞虱",
    "rice_water_weevil": "稻水象甲",
    "rice_leafhopper": "黑尾叶蝉",
    "grain_spreader_thrips": "稻蓟马",
    "rice_shell_pest": "稻负泥虫",
    # 地下害虫
    "grub": "蛴螬",
    "mole_cricket": "蝼蛄",
    "wireworm": "金针虫",
    # 夜蛾类
    "white_margined_moth": "白边地老虎",
    "black_cutworm": "小地老虎",
    "large_cutworm": "大地老虎",
    "yellow_cutworm": "黄地老虎",
    # 蛛形纲
    "red_spider": "红蜘蛛",
    # 玉米害虫
    "corn_borer": "亚洲玉米螟",
    "army_worm": "黏虫",
    # 蚜虫类
    "aphids": "棉蚜",
    "english_grain_aphid": "麦长管蚜",
    "green_bug": "麦二叉蚜",
    "bird_cherry-oataphid": "禾谷缢管蚜",
    # 甲虫类
    "Potosiabre_vitarsis": "白星花金龟",
    "peach_borer": "桃蛀螟",
    # 小麦害虫
    "wheat_blossom_midge": "麦红吸浆虫",
    "penthaleus_major": "麦圆蜘蛛",
    "longlegged_spider_mite": "麦长腿蜘蛛",
    "wheat_phloeothrips": "小麦皮蓟马",
    "wheat_sawfly": "麦叶蜂",
    "cerodonta_denticornis": "麦茎蜂",
    # 甜菜害虫
    "beet_fly": "甜菜潜叶蝇",
    "flea_beetle": "黄曲条跳甲",
    "cabbage_army_worm": "菜青虫",
    "beet_army_worm": "甜菜夜蛾",
    "Beet_spot_flies": "甜菜斑蝇",
    "meadow_moth": "草地螟",
    "beet_weevil": "甜菜象甲",
    # 苜蓿害虫
    "sericaorient_alismots_chulsky": "东方绢金龟",
    "alfalfa_weevil": "苜蓿象甲",
    "flax_budworm": "亚麻小卷蛾",
    "alfalfa_plant_bug": "苜蓿盲蝽",
    "tarnished_plant_bug": "牧草盲蝽",
    "Locustoidea": "蝗虫",
    "lytta_polita": "绿芫菁",
    "legume_blister_beetle": "豆芫菁",
    "blister_beetle": "芫菁",
    "therioaphis_maculata_Buckton": "苜蓿斑蚜",
    "odontothrips_loti": "苜蓿蓟马",
    "Thrips": "蓟马",
    "alfalfa_seed_chalcid": "苜蓿广肩小蜂",
    # 蝶蛾类
    "Pieris_canidia": "菜粉蝶",
    "Apolygus_lucorum": "绿盲蝽",
    "Limacodidae": "刺蛾",
    # 葡萄害虫
    "Viteus_vitifoliae": "葡萄根瘤蚜",
    "Colomerus_vitis": "葡萄锈壁虱",
    "Brevipoalpus_lewisi_McGregor": "刘氏短须螨",
    # 十星瓢萤叶甲
    "oides_decempunctata": "十星瓢萤叶甲",
    # 温室害虫
    "Polyphagotars_onemus_latus": "侧多食跗线螨",
    "Pseudococcus_comstocki_Kuwana": "康氏粉蚧",
    # 透翅蛾
    "parathrene_regalis": "桑透翅蛾",
    # 葡萄天蛾
    "Ampelophaga": "葡萄天蛾",
    # 斑衣蜡蝉
    "Lycorma_delicatula": "斑衣蜡蝉",
    # 天牛
    "Xylotrechus": "虎天牛",
    # 大青叶蝉
    "Cicadella_viridis": "大青叶蝉",
    # 盲蝽
    "Miridae": "盲蝽科",
    # 粉虱
    "Trialeurodes_vaporariorum": "温室白粉虱",
    # 葡萄斑叶蝉
    "Erythroneura_apicalis": "葡萄斑叶蝉",
    # 柑橘害虫
    "Papilio_xuthus": "柑橘凤蝶",
    "Panonchus_citri_McGregor": "柑橘全爪螨",
    "Phyllocoptes_oleiverus_ashmead": "柑橘锈螨",
    "Icerya_purchasi_Maskell": "吹绵蚧",
    "Unaspis_yanonensis": "矢尖蚧",
    "Ceroplastes_rubens": "红蜡蚧",
    "Chrysomphalus_aonidum": "褐圆蚧",
    "Parlatoria_zizyphus_Lucus": "黑点蚧",
    "Nipaecoccus_vastalor": "堆蜡粉蚧",
    "Aleurocanthus_spiniferus": "黑刺粉虱",
    "Tetradacus_c_Bactrocera_minax": "柑橘大实蝇",
    "Dacus_dorsalis_Hendel": "橘小实蝇",
    "Bactrocera_tsuneonis": "蜜柑大实蝇",
    # 斜纹夜蛾
    "Prodenia_litura": "斜纹夜蛾",
    "Adristyrannus": "嘴壶夜蛾",
    "Phyllocnistis_citrella_Stainton": "柑橘潜叶蛾",
    # 橘蚜
    "Toxoptera_citricidus": "橘二叉蚜",
    "Toxoptera_aurantii": "橘蚜",
    "Aphis_citricola_Vander_Goot": "绣线菊蚜",
    "Scirtothrips_dorsalis_Hood": "茶黄蓟马",
    "Dasineura_sp": "瘿蚊",
    # 芒果害虫
    "Lawana_imitata_Melichar": "白蛾蜡蝉",
    "Salurnis_marginella_Guerr": "红袖蜡蝉",
    "Deporaus_marginatus_Pascoe": "芒果切叶象",
    "Chlumetia_transversa": "芒果横线尾夜蛾",
    "Mango_flat_beak_leafhopper": "芒果扁喙叶蝉",
    "Rhytidodera_bowrinii_white": "芒果脊胸天牛",
    "Sternochetus_frigidus": "芒果果肉象甲",
    # 叶蝉
    "Cicadellidae": "叶蝉科",
}
