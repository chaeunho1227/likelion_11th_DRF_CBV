from rest_framework import serializers
from .models import *

class PostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True,required=False)
    tag = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField(read_only=True)
    like_cnt = serializers.IntegerField(read_only=True)
    dislike_cnt = serializers.IntegerField(read_only=True)

    def get_comments(self, instance):
        serializers = CommentSerializer(instance.comments, many=True)
        return serializers.data

    def get_tag(self, instance):
        tags = instance.tag.all()
        return [tag.name for tag in tags]
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = [
            'id',
            'dislike_cnt',
            'like_cnt'
            'created_at',
            'updated_at',
            'comments',
            'likes'
        ]

class PostListSerializer(serializers.ModelSerializer):
    comments_cnt =serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()
    like_cnt = serializers.IntegerField(read_only=True)
    dislike_cnt = serializers.IntegerField(read_only=True)

    def get_comments_cnt(self, instance):
        return instance.comments.count()

    def get_tag(self, instance):
        tags = instance.tag.all()
        return [tag.name for tag in tags]
    
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'writer',
            'content',
            'created_at',
            'updated_at',
            'tag',
            'image',
            'like_cnt',
            'dislike_cnt',
            'comments_cnt',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'comments_cnt',
        ]


class CommentSerializer(serializers.ModelSerializer):
    post = serializers.SerializerMethodField()
    
    def get_post(self, instance):
        return instance.post.id
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['post']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'