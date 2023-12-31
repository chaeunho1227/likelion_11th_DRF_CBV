from rest_framework import viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from .permissions import IsOwnerOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import *
from .serializers import *
# Create your views here.

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.annotate(
        like_cnt=Count(
            "reactions", filter=Q(reactions__reaction='like'), distinct=True
        ),
        dislike_cnt=Count(
            "reactions", filter=Q(reactions__reaction='dislike'), distinct=True
        ),
    )
    filter_backends = [SearchFilter]
    search_fields = ["title"]

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer
    
    def get_permissions(self):
        if self.action in ['update','destroy','partial_update']:
            return [IsOwnerOrReadOnly()]
        elif self.action in ['like','dislike']:
            return [IsAuthenticated()]
        return[]

    def get_object(self):
        obj = super().get_object()
        return obj
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        post = serializer.instance
        self.handle_tags(post)
        
        return Response(serializer.data)
    
    def handle_tags(self, post):
        words = post.content.split(' ')
        tag_list = []
        for w in words:
            if w[0] == '#':
                tag_list.append(w[1:])

        for t in tag_list:
            tag, created = Tag.objects.get_or_create(name=t)
            post.tag.add(tag)
        
        post.save()

    def perform_update(self, serializer):
        post = serializer.save()
        post.tag.clear()
        self.handle_tags(post)

    @action(methods=['GET'],detail=False)
    def biggest_likes_5(self, request):
        big_5_posts = Post.objects.annotate(like_cnt=Count("reactions", filter=Q(reactions__reaction='like'), distinct=True)).order_by('-like_cnt')[:5]
        big_5_posts_serializer = PostListSerializer(big_5_posts,many=True)
        return Response(big_5_posts_serializer.data)

    @action(methods=['GET'], detail=True)
    def like(self, request, pk=None):
        return self.like_or_dislike(request, pk, reaction="like")

    @action(methods=['GET'], detail=True)
    def dislike(self, request, pk=None):
        return self.like_or_dislike(request, pk, reaction="dislike")

    def like_or_dislike(self, request, pk=None, reaction=None):
        post = self.get_object()
        user = request.user
        existing_reaction = PostReactions.objects.filter(post=post, user=user).first()

        if reaction not in ("like", "dislike"):
            return Response()

        if existing_reaction:
            if existing_reaction.reaction == reaction:
                existing_reaction.delete()
                return Response()
            else:
                existing_reaction.reaction = reaction
                existing_reaction.save()
                return Response()
        else:
            PostReactions.objects.create(post=post, user=user, reaction=reaction)
            return Response()

class CommentViewSet(viewsets.GenericViewSet,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,mixins.DestroyModelMixin):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_permissions(self):
        if self.action in ['update','destroy','partial_update']:
            return [IsOwnerOrReadOnly()]
        return[]

    def get_object(self):
        obj = super().get_object()
        return obj
    
class PostCommentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        post = self.kwargs.get("post_id")
        queryset = Comment.objects.filter(post_id=post)
        return queryset

    def list(self, request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        queryset = self.filter_queryset(self.get_queryset().filter(post=post))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, post_id=None):
        post = get_object_or_404(Post, id=post_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post)
        return Response(serializer.data)


class TagViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "name"
    lookup_url_kwarg = "tag_name"

    def retrieve(self, request, *args, **kwargs):
        tag_name = kwargs.get("tag_name")
        tag = get_object_or_404(Tag, name=tag_name)
        posts = Post.objects.filter(tag=tag)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)
