"""
该模块定义了有关用户资料、用户行为、番剧剧集、自定义条目的数据库模型。
"""

from django.db import models
from django.contrib.auth.models import User#引入Django自带的用户模型，方便认证和权限管理

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta
"""
用户管理：用户资料、关注关系
"""
#为每个注册用户登记基本信息
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)#通过与User模型一对一关联扩展用户信息，详细包含项查询https://docs.djangoproject.com/zh-hans/5.2/ref/contrib/auth/
    cellphone = models.CharField(max_length=20, blank=True)
    
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    signature = models.CharField(max_length=100, blank=True)
    intro = models.TextField(blank=True,null=True)

    def __str__(self):#调试时显示实例的名字（即user.username）方便辨认
        return self.user.username

#用户关注关系
class UserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      constraints = [
          models.UniqueConstraint(fields=["follower", "following"], name="unique_user_follow")#确保同一用户不能重复关注同一用户
      ]

class PrivacySetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

  
    followings = models.CharField(max_length=20, default="public")   # 关注列表
    followers = models.CharField(max_length=20, default="public")    # 粉丝列表
    watchlist = models.CharField(max_length=20, default="public")    # 追番列表
    activities = models.CharField(max_length=20, default="public")   # 动态流

    def __str__(self):
        return f"{self.user.username} 的隐私设置"

"""

番剧和剧集管理：番剧信息、剧集详情、追番状态
"""
class Anime(models.Model):
    external_id = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        help_text="外部数据源的唯一标识，便于去重同步",
    )
    title = models.CharField(max_length=512)
    title_cn = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    release_date = models.DateField(null=True)
    airtime = models.CharField(max_length=20, blank=True)  # 播放时段

    # 图片和识别码
    cover_image = models.ImageField(upload_to='covers/', blank=True)
    cover_url = models.URLField(blank=True, default="")
    uid = models.CharField(max_length=20, blank=True)  # (ISBN/IMDB编号) 
    # 统计数据
    rating = models.FloatField(default=0.0)          
    popularity = models.IntegerField(default=0)      
    wishes = models.IntegerField(default=0)         # 想看人数
    collections = models.IntegerField(default=0)    # 收藏人数
    doing = models.IntegerField(default=0)           # 在看人数
    on_hold = models.IntegerField(default=0)        # 搁置人数
    dropped = models.IntegerField(default=0)         # 抛弃人数
    status = models.CharField(max_length=32, blank=True)
    total_episodes = models.IntegerField(default=0)

    # 元数据
    genres = models.JSONField(default=list, blank=True)
    platform = models.CharField(max_length=50, blank=True)  
    is_series = models.BooleanField(default=False)
    nsfw = models.BooleanField(default=False)        #是否成人内容
    is_banned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=True)
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # 创建者
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='animes_created')

    season_year = models.IntegerField(null=True, blank=True, help_text="季度番所在年份，例如 2025")
    season_quarter = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="季度番季度：spring/summer/autumn/winter"
    )

    # 新增：推荐打标（方便推荐接口查询）
    is_season_featured = models.BooleanField(default=False, help_text="是否为当前季度推荐番")
    is_weekly_featured = models.BooleanField(default=False, help_text="是否为本周推荐番")

    def __str__(self):
        return self.title


class Episode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    episode_number = models.IntegerField()
    title = models.CharField(max_length=200)
    title_cn = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    #播放信息
    release_date = models.DateField(null=True)
    duration = models.CharField(max_length=20, blank=True)
    online_urls = models.TextField(blank=True)#存储多个播放链接，格式可为JSON或分行文本

    #分类信息
    episode_type = models.IntegerField(default=1)    #(正片/OVA等)
    disc_number = models.IntegerField(default=0)     #碟片数

    #统计数据
    rating = models.IntegerField(default=0) 
    comments = models.IntegerField(default=0)
    resources = models.IntegerField(default=0)

    # 状态管理
    is_locked = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["anime", "episode_number"], name="unique_anime_episodeNumber")#确保同一番剧的集数不重复
      ]

#追番状态
class WatchStatus(models.Model):
    STATUS_CHOICES = [
        ("WANT", "想看"),
        ("WATCHING", "在看"),
        ("FINISHED", "已看"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
          models.UniqueConstraint(fields=["user", "anime"], name="unique_user_anime")
      ]

"""
用户创建内容：自定义条目、评价、回复、点赞、举报
"""
#已复用anime组件作为自定义条目的基础模型

#评价，由于涉及多种评价对象，采用GenericForeignKey实现多态关联
class Comment(models.Model):  
    SCORE_CHOICES = [(i, str(i)) for i in range(1, 11)]
    #使用GenericForeignKey支持多类型对象
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(choices=SCORE_CHOICES)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)

    # 添加评论范围标识
    COMMENT_SCOPE = [
      ('ANIME', '番剧评论'),
      ('EPISODE', '剧集评论'),
      ('CHARACTER', '角色评论'),
      ('PERSON', '人物评论'),
      ('ITEM', '条目评论'),
    ]
    scope = models.CharField(max_length=10, choices=COMMENT_SCOPE, default='ANIME')

    def __str__(self):
        return f"{self.user.username} - {self.score}分"

# 对评价的回复
class Reply(models.Model):  
    review = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # 用于软删除，实现取消点赞功能

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "comment"], name="unique_user_comment")#确保同一用户对同一评论只能有一个点赞记录
        ]

    def __str__(self):
        return f"{self.user.username} {'点赞' if self.is_active else '取消点赞'} {self.comment}"


class Report(models.Model):
    # 举报分类
    REPORT_CATEGORIES = [
        ('SPAM', '垃圾广告'),
        ('HARASSMENT', '违法违规'),
        ('INAPPROPRIATE', '人身攻击'),
        ('SPOILER', '剧透内容'),
        ('OTHER', '其他')
    ]

    # 处理状态
    STATUS_CHOICES = [
        ('PENDING', '待处理'),
        ('RESOLVED', '已处理'),
        ('REJECTED', '已驳回')
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_created',verbose_name='举报人')
    # 被举报目标（通用外键）(注：可被举报的对象实际上只有条目/评论/对评论的回复)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    # 举报内容
    category = models.CharField(max_length=20, choices=REPORT_CATEGORIES)
    reason = models.TextField(blank=True, help_text="详细说明举报原因")
    created_at = models.DateTimeField(auto_now_add=True)

    # 审核处理信息
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    moderator = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reports_handled',
        verbose_name='处理人'
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True, help_text="处理结果或管理员备注")

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
        ordering = ['-created_at']
        verbose_name = "用户举报"
        verbose_name_plural = "举报记录"

    def __str__(self):
        return f"{self.reporter.username}举报{self.content_type}({self.object_id})"

"""
角色阵容与制作团队
"""
#人物主表，包含现实中的个人或团体
class Person(models.Model):
    pers_id=models.AutoField(primary_key=True)
    pers_name=models.CharField(max_length=255) 
    pers_type=models.PositiveSmallIntegerField(help_text="个人/公司/组合")
    pers_info=models.TextField(blank=True, null=True)

    #以下为可选角色标签
    is_producer = models.BooleanField(default=False)
    is_mangaka = models.BooleanField(default=False)#漫画家
    is_artist = models.BooleanField(default=False)
    is_seiyu = models.BooleanField(default=False)#声优
    is_writer = models.BooleanField(default=False)
    is_illustrator = models.BooleanField(default=False)#插画师
    is_actor = models.BooleanField(default=False)

    summary=models.TextField()#人物介绍
    pers_img=models.CharField(max_length=255)#图片路径

    comment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lastpost = models.DateTimeField(auto_now_add=True)#最近的用户评论日期。

    lock = models.SmallIntegerField(default=0)
    anidb_id = models.PositiveIntegerField(default=0)#编辑锁定
    ban = models.PositiveSmallIntegerField(default=0) 
    redirect = models.PositiveIntegerField(default=0)#重定向到其他人物ID 
    nsfw = models.BooleanField(default=False)#“包含成人内容”标识

 #虚拟角色主表
class Character(models.Model):
    ROLE_CHOICES = [
        (1, '角色'),
        (2, '机体'),
        (3, '组织'),
    ]

    name = models.CharField(max_length=255, verbose_name='角色名')
    role_type = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=1, verbose_name='角色类型')
    summary = models.TextField(blank=True, verbose_name='角色简介')
    infobox = models.TextField(blank=True, verbose_name='信息框内容')
    image = models.CharField(max_length=255, blank=True, verbose_name='角色头像路径')

    # 统计数据
    comment_count = models.PositiveIntegerField(default=0)
    collect_count = models.PositiveIntegerField(default=0)

    # 时间戳与状态
    created_at = models.DateTimeField(auto_now_add=True)
    last_commented_at = models.DateTimeField(null=True, blank=True)
    lock = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_nsfw = models.BooleanField(default=False)
    redirect_to = models.PositiveIntegerField(default=0, help_text="重定向角色ID，如角色合并")

    # 补充字段（对应 chii_person_fields）
    gender_choices = [
        (0, '未知'),
        (1, '男性'),
        (2, '女性'),
        (3, '其他'),
    ]
    gender = models.PositiveSmallIntegerField(choices=gender_choices, default=0)
    blood_type = models.PositiveSmallIntegerField(default=0, help_text='血型代号：0=未知,1=A,2=B,3=O,4=AB')
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_month = models.PositiveSmallIntegerField(null=True, blank=True)
    birth_day = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'characters'
        verbose_name = '虚拟角色'
        verbose_name_plural = '角色表'

    def __str__(self):
        return self.name


"""
以下内容为关联表
"""


"""角色与番剧条目的多对多关系表"""
class CharacterAppearance(models.Model):
    CHARACTER_ROLE = [
        (1, '主角'),
        (2, '配角'),
        (3, '客串'),
    ]

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='appearances')
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE, related_name='character_appearances')
    role = models.PositiveSmallIntegerField(choices=CHARACTER_ROLE, default=2)
    appear_eps = models.TextField(blank=True, help_text='角色出现的集数描述（可选）')
    order = models.PositiveSmallIntegerField(default=0, help_text='角色展示顺序')

    class Meta:
        db_table = 'character_appearance'
        unique_together = ('character', 'anime')
        verbose_name = '角色出演记录'
        verbose_name_plural = '角色出演记录表'

    def __str__(self):
        return f"{self.character.name} - {self.get_role_display()} @ {self.anime.title}"


"""角色与现实声优(Person)的关系表"""
class CharacterVoice(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='voices')
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='voiced_characters')
    note = models.CharField(max_length=100, blank=True, help_text='备注：语言或版本，如“日语配音”')

    class Meta:
        db_table = 'character_voice'
        unique_together = ('character', 'person')
        verbose_name = '角色声优'
        verbose_name_plural = '角色声优表'

    def __str__(self):
        return f"{self.character.name} 由 {self.person.pers_name} 配音"

"""制作职能分类，如导演、脚本、音乐、出品等"""
class StaffRole(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_voice_role = models.BooleanField(default=False, help_text="是否为声优类职能")#用于将声优关联到角色表上

    class Meta:
        db_table = "staff_roles"
        verbose_name = "制作职能"
        verbose_name_plural = "制作职能表"

    def __str__(self):
        return self.name

"""番剧与现实人物(Person)的关系表"""
class AnimeStaff(models.Model):
    anime = models.ForeignKey('Anime', on_delete=models.CASCADE, related_name='staff_members')
    person = models.ForeignKey('Person', on_delete=models.CASCADE, related_name='staff_works')
    role = models.ForeignKey('StaffRole', on_delete=models.PROTECT, related_name='staff_assignments')

    # 若是声优，则可选关联角色（Character）
    character = models.ForeignKey('Character', on_delete=models.SET_NULL, null=True, blank=True, related_name='voice_actors')

    order = models.PositiveSmallIntegerField(default=0, help_text='展示顺序')
    note = models.CharField(max_length=100, blank=True, help_text='附加信息：如语言、版本')

    class Meta:
        db_table = 'anime_staff'
        unique_together = ('anime', 'person', 'role', 'character')
        verbose_name = '番剧制作人员'
        verbose_name_plural = '番剧制作人员表'

    def __str__(self):
        role_name = self.role.name
        return f"{self.person.pers_name} - {role_name} @ {self.anime.title}"


"""验证码存储表，用于注册/找回密码等功能"""
class VerificationCode(models.Model):
    target = models.CharField(max_length=100, unique=True)  # 手机号或邮箱
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() - self.created_at > timedelta(minutes=5)  # 5分钟有效期

    def __str__(self):
        return f"{self.target} -> {self.code}"



"""
Activity / Feed（用户动态流）
"""
class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    ACTION_CHOICES = [
        ('COMMENT', '创建了评论'),
        ('LIKE', '点赞了对象'),
        ('WATCH', '新增追番'),
        ('ITEM', '新建了条目'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'])]
        verbose_name = "用户动态"
        verbose_name_plural = "用户动态流"

"""
同步日志模型
"""
class SyncLog(models.Model):
    class JobType(models.TextChoices):
        SEASON = "season", "季度番同步"
        WEEKLY = "weekly", "周合集生成"

    class Status(models.TextChoices):
        PENDING = "pending", "进行中"
        SUCCESS = "success", "成功"
        FAILURE = "failure", "失败"

    # 兼容旧字段：保留 sync_type 并用 job_type 进行标准化
    sync_type = models.CharField(max_length=20, choices=JobType.choices)
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.WEEKLY
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True, default="")  # 可以存异常信息、统计信息等

    class Meta:
        ordering = ["-started_at"]

""""
通知模型
"""
# class Notification(models.Model):
#     recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
#     sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
#     content = models.CharField(max_length=255)
#     link = models.CharField(max_length=255, blank=True, help_text="可选：跳转链接")
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created_at']
#         verbose_name = "通知"
#         verbose_name_plural = "通知表"

#     def __str__(self):
#         return f"To {self.recipient.username}: {self.content}"

"""
Tag(番剧标签模型)
"""
# class Tag(models.Model):
#     name = models.CharField(max_length=50, unique=True)
#     description = models.TextField(blank=True)

#     class Meta:
#         verbose_name = "标签"
#         verbose_name_plural = "标签表"

#     def __str__(self):
#         return self.name


# class AnimeTag(models.Model):
#     anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='tags')
#     tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = ('anime', 'tag')
#         verbose_name = "番剧标签关联"
#         verbose_name_plural = "番剧标签关联表"
